from datetime import datetime,timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from authlib.jose import jwt, JoseError # 生成用于验证的token
from flask import current_app
from flask_avatars import Identicon
from markdown import markdown
import bleach

from . import db
from . import login_manager

'''加载用户的函数'''
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


'''应用中的各项权限'''
class Permission:
    FOLLOW = 1
    COMMENT = 2
    WRITE = 4
    MODERATE = 8
    ADMIN = 16


class Role(db.Model):     
    __tablename__ = 'roles'     
    id = db.Column(db.Integer, primary_key=True)     
    name = db.Column(db.String(64), unique=True) 
    default = db.Column(db.Boolean, default=False, index=True) # 默认角色是注册新用户时赋予用户的角色。因为应用将在 roles 表中搜索默认角色，所以我们为这一列设置了索引，提升搜索的速度。
    permissions = db.Column(db.Integer) 
    users = db.relationship('User', backref='role', lazy='dynamic') 
    
    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0
    
    '''权限管理'''
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm): # 检 查组合权限是否包含指定的单独权限
        return self.permissions & perm == perm

    '''在数据库中创建角色'''
    @staticmethod
    def insert_roles():
        roles = {
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE],
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                        Permission.WRITE, Permission.MODERATE],
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                        Permission.WRITE, Permission.MODERATE, Permission.ADMIN],
        }
        default_role = 'User'
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None: # 没有这个角色时候再创建
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):         
        return '<Role %r>' % self.name  
        

class Post(db.Model):     
    __tablename__ = 'posts'     
    id = db.Column(db.Integer, primary_key=True)     
    body = db.Column(db.Text)   
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)     
    author_id = db.Column(db.Integer, db.ForeignKey('users.id')) 

    '''在Post模型中处理Markdown文本'''
    @staticmethod     
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


db.event.listen(Post.body, 'set', Post.on_changed_body)

'''为了能在关系中处理自定义的数据，我们必须提升关联表的地位，使其变成应用可访问的模型。
SQLAlchemy不能直接使用这个关联表，因为如果这么做应用就无法访问其中的自定义字段。相反地，
要把这个多对多关系的左右两侧拆分成两个基本的一对多关系，而且要定义成标准的关系'''
class Follow(db.Model):
    __tablename__ = 'follows'
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)     
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),primary_key=True)     
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

        
class User(UserMixin, db.Model):     # 修改 User 模型，支持用户登录
    __tablename__ = 'users'     
    id = db.Column(db.Integer, primary_key=True)     
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True) 
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id')) 
    confirmed = db.Column(db.Boolean, default=False)
    name = db.Column(db.String(64))     
    location = db.Column(db.String(64))     
    about_me = db.Column(db.Text())     
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)     
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow) 
    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))
    avatar_raw = db.Column(db.String(64))
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    followed = db.relationship('Follow', foreign_keys=[Follow.follower_id],
                                backref=db.backref('follower', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')     
    followers = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FBLOG_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        self.generate_avatar()

    def __repr__(self):         
        return '<User %r>' % self.username

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        header = {'typ': 'jwt','alg':'HS256'}
        key = current_app.config['SECRET_KEY']
        data = {
            'confirm':self.id, 
            'iat':datetime.utcnow(),
            }
        if expiration:
            data['exp'] = data['iat'] + timedelta(seconds=expiration)
        return jwt.encode(header=header, payload=data,key=key).decode('utf-8')
        #return s.dumps({'confirm':self.id}).decode('utf-8')

    def confirm(self, token):
        key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, key)
            data.validate() # 检测token
        except JoseError:   # 捕获异常
            print('JoseError')
            return False
        if data.get('confirm') != self.id:
            print('data.confirm != self.id')
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self,  expiration=3600):
        header = {'typ': 'jwt','alg':'HS256'}
        key = current_app.config['SECRET_KEY']
        data = {
            'reset':self.id ,
            'iat':datetime.utcnow(),
            }
        if expiration:
            data['exp'] = data['iat'] + timedelta(seconds=expiration)
        return jwt.encode(header=header, payload=data,key=key).decode('utf-8')

    @staticmethod
    def reset_password(token, new_password):
        key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, key)
            data.validate() # 检测token
        except JoseError:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True

    def generate_change_email_token(self, new_email,  expiration=3600):
        header = {'typ': 'jwt','alg':'HS256'}
        key = current_app.config['SECRET_KEY']
        data = {
            'change_email':self.id, 
            'new_email':new_email, 
            'iat':datetime.utcnow(),
            }
        if expiration:
            data['exp'] = data['iat'] + timedelta(seconds=expiration)
        return jwt.encode(header=header, payload=data,key=key).decode('utf-8')


    def change_email(self, token):
        key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, key)
            data.validate() # 检测token
        except JoseError:
            return False
        if data.get('change_email') != self.id:
            return False
        
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        
        self.email = new_email
        db.session.add(self)
        return True

    '''检查用户是否有指定的权限'''
    def can(self, perm):         
        return self.role is not None and self.role.has_permission(perm)      
            
    def is_administrator(self):         
        return self.can(Permission.ADMIN) 

    def ping(self):   # 刷新用户的最后访问时间      
        self.last_seen = datetime.utcnow()         
        db.session.add(self)         
        db.session.commit()

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        #db.session.add(self)
        db.session.commit()

    def follow(self, user):         
        if not self.is_following(user):             
            f = Follow(follower=self, followed=user)             
            db.session.add(f)      
            
    def unfollow(self, user):         
        f = self.followed.filter_by(followed_id=user.id).first()         
        if f:             
            db.session.delete(f)     
            
    def is_following(self, user):         
        if user.id is None:             
            return False         
        return self.followed.filter_by(followed_id=user.id).first() is not None      
        
    def is_followed_by(self, user):         
        if user.id is None:             
            return False         
        return self.followers.filter_by(follower_id=user.id).first() is not None

    '''获取所关注用户的文章'''
    @property
    def followed_posts(self):         
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)


class AnonymousUser(AnonymousUserMixin):  
    def can(self, permissions):         
        return False      
        
    def is_administrator(self):         
        return False 

''' Flask-Login使用应用自定义的匿名用户类。'''     
login_manager.anonymous_user = AnonymousUser