from flask import Blueprint

# 创建news蓝图对象
user_blue = Blueprint("user", __name__, url_prefix="/user")

# 关联视图和蓝图
from .views import *