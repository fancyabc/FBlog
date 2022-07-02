
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from authlib.jose import jwt, JoseError # 生成用于验证的token
from flask import current_app

from . import db
from . import login_manager

'''加载用户的函数'''
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Role(db.Model):     
    __tablename__ = 'roles'     
    id = db.Column(db.Integer, primary_key=True)     
    name = db.Column(db.String(64), unique=True)  
    users = db.relationship('User', backref='role')    
    
    def __repr__(self):         
        return '<Role %r>' % self.name  
        
        
class User(UserMixin, db.Model):     # 修改 User 模型，支持用户登录
    __tablename__ = 'users'     
    id = db.Column(db.Integer, primary_key=True)     
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True) 
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id')) 
    confirmed = db.Column(db.Boolean, default=False) 

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

    def generate_confirmation_token(self, **kwargs):
        header = {'alg':'HS256'}
        key = current_app.config['SECRET_KEY']
        data = {'confirm':self.id}
        data.update(**kwargs)
        return jwt.encode(header=header, payload=data,key=key)
        #return s.dumps({'confirm':self.id}).decode('utf-8')

    def confirm(self, token):
        key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, key)
        except JoseError:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def generate_reset_token(self, **kwargs):
        header = {'alg':'HS256'}
        key = current_app.config['SECRET_KEY']
        data = {'reset':self.id}
        data.update(**kwargs)
        return jwt.encode(header=header, payload=data,key=key)

    @staticmethod
    def reset_password(token, new_password):
        key = current_app.config['SECRET_KEY']
        try:
            data = jwt.decode(token, key)
        except JoseError:
            return False
        user = User.query.get(data.get('reset'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        return True