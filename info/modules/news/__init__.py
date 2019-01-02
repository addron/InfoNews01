from flask import Blueprint

# 创建news蓝图对象
news_blue = Blueprint("news", __name__, url_prefix="/news")

# 关联视图和蓝图
from .views import *
