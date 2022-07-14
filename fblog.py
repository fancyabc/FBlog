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
from flask_migrate import Migrate, upgrade

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
@click.argument('test_names', nargs=-1)
def test(coverage, test_names):     
    """Run the unit tests."""
    if coverage and not os.environ.get('FLASK_COVERAGE'):         
        os.environ['FLASK_COVERAGE'] = '1'         
        os.execvp(sys.executable, [sys.executable] + sys.argv)

    import unittest 
    if test_names:
        tests = unittest.TestLoader().loadTestsFromNames(test_names)
    else:    
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


@app.cli.command() 
@click.option('--length', default=25, help='Number of functions to include in the profiler report.') 
@click.option('--profile-dir', default=None,help='Directory where profiler data files are saved.') 
def profile(length, profile_dir):     
    """Start the application under the code profiler."""     
    from werkzeug.middleware.profiler import ProfilerMiddleware     
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],profile_dir=profile_dir)     
    app.run(debug=False)


'''创建或更新数据库表。'''
@app.cli.command()
def deploy():     
    """Run deployment tasks."""     
    # 把数据库迁移到最新修订版本     
    upgrade()      
    # 创建或更新用户角色     
    Role.insert_roles()      
    # 确保所有用户都关注了他们自己     
    User.add_self_follows()


if __name__ == "__main__":
    app.cli()