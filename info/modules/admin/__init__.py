from flask import Blueprint

# 创建admin蓝图对象
admin_blue = Blueprint("admin", __name__, url_prefix="/admin")


# 添加蓝图请求钩子，只针对注册蓝图进行监听
@admin_blue.before_request
def check_superuser():
    is_admin = session.get("is_admin")
    if not is_admin and not request.url.endswith(url_for("admin.login")):
        return redirect(url_for("home.index"))


# 关联视图和蓝图
from .views import *
