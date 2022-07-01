from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email

"""
Note: 2.3.0以后的WTForms已经不支持email验证器了，而此处用来建立表单的flask-wtf是集成了wtforms的，所以也是没有该验证器的了。
需要再自行下载包
 pipenv install email-validator
"""
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1,64),Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')