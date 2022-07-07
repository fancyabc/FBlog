from crypt import methods
import email
from lib2to3.pgen2 import token
from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User
from .forms import ChangeEmailForm, LoginForm, RegistrationForm, ChangePasswordForm, ResetPasswordRequest, ResetPasswordForm
from .. import db
from ..email import send_email


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('Invalid username or password.')
    return render_template('auth/login.html', form= form)



@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Comfirm Your Account',
                    'auth/email/confirm',user=user, token=token) # 发送确认邮件
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


'''用户点击确认邮件中的链接后，要先登录，然后才能执行这个视图函数。'''
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token): # token 验证成功
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')     
    return redirect(url_for('main.index'))


'''使用 before_app_request 处理程序过滤未确认的账户,更新已登录用户的最后访问时间'''
@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if  not current_user.confirmed \
            and request.endpoint \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed') 
def unconfirmed():     
    if current_user.is_anonymous or current_user.confirmed:     # 匿名登录或者已经验证的用户，去首页    
        return redirect(url_for('main.index'))     
    return render_template('auth/unconfirmed.html') # 否则显示未验证页面，然后可以选择点击发送验证邮件


'''重新发送账户确认邮件'''
@auth.route('/confirm') 
@login_required # 需要在登录状态下
def resend_confirmation():     
    token = current_user.generate_confirmation_token()     
    send_email(current_user.email, 'Confirm Your Account',                
                'auth/email/confirm', user=current_user, token=token)     
    flash('A new confirmation email has been sent to you by email.')     
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.add(current_user)
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid password')
    return render_template('auth/change_password.html', form=form)


'''为避免用户忘记密码后无法登入，应用可以提供重设密码功能。为了安全起见，
有必要使用令牌，类似于确认账户时用到的。用户请求重设密码后，应用向用户
注册时提供的电子邮件地址发送一封包含重设令牌的邮件。用户点击邮件中的链接，
令牌通过验证后，显示一个用于输入新密码的表单。'''
@auth.route('/reset', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequest()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:    # 确有其人
            token = user.generate_reset_token() 
            send_email(user.email, 'Reset Your Password',                
                'auth/email/reset_password', user=user, token=token)     
            flash('An email with instructions to reset your password has been sent to you by email.')     
            return redirect(url_for('auth.login'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.reset_password(token, form.password.data):
            db.session.commit()
            flash('Your password has been updated.')
            return redirect(url_for('auth.login'))
        else:
            return redirect(url_for('main.index'))
    return render_template('auth/reset_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            new_email = form.email.data.lower()
            token = current_user.generate_change_email_token(new_email) 
            send_email(new_email, 'Confirm Your Email Address',                
                'auth/email/change_email', user=current_user, token=token)     
            flash('A confirmation email has been sent to you by email.')     
            return redirect(url_for('main.index'))
        flash('Invalid email address or password')
    return render_template('auth/change_email.html', form=form)


@auth.route('/change_email/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        db.session.commit()
        flash('Your email has been changed.')
    else:
        flash('Your email has been changed.')
    return redirect(url_for('main.index'))