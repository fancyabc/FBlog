from flask_wtf import FlaskForm
from flask_pagedown.fields import PageDownField
from wtforms import StringField, SubmitField, TextAreaField,BooleanField,SelectField,HiddenField
from wtforms.validators import DataRequired,Length, Regexp,Email
from wtforms import ValidationError
from ..models import User, Role


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


'''用户资料编辑表单'''
class EditProfileForm(FlaskForm):
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')


'''管理员使用的资料编辑表单'''
class EditProfileAdminForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),Email()])
    username = StringField('Username', validators=[
                            DataRequired(), Length(1, 64),
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                            'Usernames must have only letters, numbers, dots or '
                            'underscores')]) 
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int) # 用于角色选择的下拉列表.元组中的标识符是角色的id，因为这是个整数，所以在SelectField构造函数中加上了coerce=int参数，把字段的值转换为整数
    name = StringField('Real name', validators=[Length(0,64)])
    location = StringField('Location', validators=[Length(0,64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Register')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__( *args, **kwargs)
        self.choices =  [(role.id, role.name) for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email rlready registered')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in user.')

'''博客文章表单：支持Markdown的文章表单'''
class PostForm(FlaskForm):     
    body = PageDownField("What's on your mind?", validators=[DataRequired()])     
    submit = SubmitField('Submit')