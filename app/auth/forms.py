from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from ..models import User

"""
Note: 2.3.0以后的WTForms已经不直接支持Email()验证器了，而此处用来建立表单的flask-wtf是集成了wtforms的，所以也是没有该验证器的了。
需要再自行下载包
 pipenv install email-validator
"""
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')


class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),Email()])
    username = StringField('Username', validators=[
                            DataRequired(), Length(1, 64),
                            Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0,
                            'Usernames must have only letters, numbers, dots or '
                            'underscores')]) 
    password = PasswordField('Password', validators=[DataRequired(),
                            EqualTo('password2', message='Passwords must match.')])
    password2 = PasswordField('Comfirm password', validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered!')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('username already in use!')