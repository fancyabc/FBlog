'''应用包的构造文件'''


from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config

"""创建扩展类时没有向构造函数传入参数，因此扩展并未真正初始化。"""
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()

"""create_app() 函数是应用的工厂函数，接受一个参数，是应用使用的配置名。"""
def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app