import time
from datetime import datetime, timedelta

from flask import url_for, request, session, redirect, render_template, current_app, g, abort
from info.modules.admin import admin_blue
from info.utils.common import user_login_data
from info.utils.constants import USER_COLLECTION_MAX_NEWS
from info.utils.models import User


# 首页
@admin_blue.route('/index')
@user_login_data
def index():
    user = g.user
    return render_template("admin/index.html", user=user.to_dict())


# 登陆
@admin_blue.route('/login', methods=['GET', 'POST'])
def login():
    # 展示页面
    if request.method == 'GET':
        # 取出session
        user_id = session.get("user_id")
        is_admin = session.get("is_admin")
        if user_id and is_admin:  # 管理员已登录, 重定向到后台首页
            return redirect(url_for("admin.index"))
        return render_template("admin/login.html")

    # POST 提交资料
    # 获取参数
    username = request.form.get("username")
    password = request.form.get('password')

    # 校验参数
    if not all([username, password]):
        # return render_template("admin/login.html", errmsg="参数不足")
        return render_template("admin/login.html", errmsg="参数不足qqqq")

    # 获取管理员用户数据
    try:
        user = User.query.filter(User.mobile == username, User.is_admin == True).first()
    except BaseException as e:
        current_app.logger.error(e)
        return render_template("admin/login.html", errmsg="数据库操作失败")

    # 判断用户是否存在
    if not user:
        return render_template("admin/login.html", errmsg="管理员不存在")

    # 校验密码
    if not user.check_password(password):
        return render_template("admin/login.html", errmsg="账号/密码错误")

    # 保存session数据，免密码登陆
    session['user_id'] = user.id
    session['is_admin'] = True

    # 校验成功，重定向到后台首页
    return redirect(url_for("admin.index"))


# 退出登陆
@admin_blue.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_admin', None)

    # 重定向到后台登录
    return redirect(url_for("admin.login"))


# 用户统计
@admin_blue.route('/user_count')
def user_count():
    # 用户总数
    try:
        total_count = User.query.filter(User.is_admin == False).count()
    except BaseException as e:
        current_app.logger.error(e)
        total_count = 0

    # 月新增 注册时间是关键 要大于本月1号0点  timedetail

    # 获取当前时间的年月
    t = time.localtime()

    # 构建日期字符串  2019-01-01
    mon_date_str = "%d-%02d-01" % (t.tm_year, t.tm_mon)

    # 转换为日期对象  strptime 是转换为日期对象   strftime是转为字符串
    mon_date = datetime.strptime(mon_date_str, "%Y-%m-%d")

    try:
        mon_count = User.query.filter(User.is_admin == False, User.create_time >= mon_date).count()
    except BaseException as e:
        current_app.logger.error(e)
        mon_count = 0

    # 日新增  当天0点
    day_date_str = "%d-%02d-%02d" % (t.tm_year, t.tm_mon, t.tm_mday)
    day_date = datetime.strptime(day_date_str, "%Y-%m-%d")

    try:
        day_count = User.query.filter(User.is_admin == False, User.create_time >= day_date).count()
    except BaseException as e:
        current_app.logger.error(e)
        day_count = 0

    # 某天的注册人数  注册时间从当天的0点  到次日的0点  timedelta 是时间间隔
    active_count = []
    active_time = []

    for i in range(0, 30):
        begin_date = day_date - timedelta(days=i)  # 30天中的任意一天0点
        end_date = begin_date + timedelta(days=1)  # 次日0点
        try:
            one_day_count = User.query.filter(User.is_admin == False, User.create_time >= begin_date,
                                              User.create_time < end_date).count()
            active_count.append(one_day_count)

            # 将日期转换为字符串  strftime
            one_day_str = begin_date.strftime("%Y-%m-%d")
            active_time.append(one_day_str)
        except BaseException as e:
            current_app.logger.error(e)
            one_day_count = 0

    active_time.reverse()
    active_count.reverse()

    data = {
        "total_count": total_count,
        "mon_count": mon_count,
        "day_count": day_count,
        "active_count": active_count,
        "active_time": active_time
    }

    return render_template("admin/user_count.html", data=data)


# 用户列表 要用User
@admin_blue.route('/user_list')
def user_list():
    # 获取参数
    p = request.args.get("p", 1)

    # 校验
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)

    # 查询用户表　User
    try:
        pn = User.query.paginate(p, USER_COLLECTION_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    # 返回json
    data = {
        "user_list": [user.to_admin_dict() for user in pn.items],
        "cur_page": pn.page,
        "total_page": pn.pages
    }

    return render_template("admin/user_list.html",data=data)
