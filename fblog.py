import os
import sys
import click

COV = None 
if os.environ.get('FBLOG_COVERAGE'):     
    import coverage     
    COV = coverage.coverage(branch=True, include='app/*')     
    COV.start()

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
@click.option('--coverage/--no-coverage', default=False,help='Run tests under code coverage.')
def test(coverage):     
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):         
        os.environ['FLASK_COVERAGE'] = '1'         
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest     
    tests = unittest.TestLoader().discover('tests')     
    unittest.TextTestRunner(verbosity=2).run(tests)

    if COV:         
        COV.stop()         
        COV.save()         
        print('Coverage Summary:')         
        COV.report()         
        basedir = os.path.abspath(os.path.dirname(__file__))         
        covdir = os.path.join(basedir, 'tmp/coverage')         
        COV.html_report(directory=covdir)         
        print('HTML version: file://%s/index.html' % covdir)         
        COV.erase()