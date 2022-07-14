import os

from app import create_app, db
from app.models import User, Role, Follow, Permission, Post, Comment
from flask_migrate import Migrate

'''先创建一个应用实例。如果已经定义了环境变量 FLASK_CONFIG，则从中读取配置名；
否则使用默认配置。然后初始化 Flask-Migrate 和为 Python shell 定义的上下文。'''
app = create_app(os.getenv('FBLOG_CONFIG') or'default')
migrate = Migrate(app, db)

'''把对象添加到导入列表中'''
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role, Permission=Permission,
        Follow=Follow, Post=Post, Comment=Comment)


@app.cli.command() 
def test():     
    """Run the unit tests."""     
    import unittest     
    tests = unittest.TestLoader().discover('tests')     
    unittest.TextTestRunner(verbosity=2).run(tests)