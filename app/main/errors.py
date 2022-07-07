from flask import render_template

from . import main

@main.app_errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

'''要想注册应用全局的错误处理程序，必须使用 app_errorhandler装饰器。'''
@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500