# from ensurepip import bootstrap
from crypt import methods
from datetime import datetime

from flask import Flask, render_template, session, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)

'''app.config 字典可用于存储 Flask、扩展和应用自身的配置变量。
使用标准的字典句法就能把配置添加到 app.config 对象中。
这个对象还提供了一些方法，可以从文件或环境中导入配置。'''
app.config['SECRET_KEY'] = 'hard to guess string' # 配置 Flask-WTF

bootstrap = Bootstrap(app)
moment = Moment(app)  # 初始化 Flask-Moment


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')

@app.route('/', methods = ['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        if old_name is not None and old_name != form.name.data:
            flash('Looks you have changed your name!')
        session['name'] = form.name.data
        return redirect(url_for('index'))
    return render_template('index.html',form=form,name=session.get('name'))


@app.route('/user/<name>')
def user(name):
    return render_template('user.html', name=name)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500