from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission

'''在模板中可能也需要检查权限，所以 Permission 类的所有常量要能在模板中访问。
为了避免每次调用 render_template() 时都多添加一个模板参数，可以使用上下文处理器。
在渲染时，上下文处理器能让变量在所有模板中可访问'''

@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)