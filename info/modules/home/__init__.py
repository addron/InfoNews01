from flask import Blueprint

# 创建蓝图对象
home_blue = Blueprint("home", __name__)

from .views import *
