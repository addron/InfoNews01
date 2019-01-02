from flask import render_template, g, redirect, url_for, abort, request, jsonify, current_app

from info.modules.user import user_blue
from info.utils.common import user_login_data, file_upload
from info.utils.response_code import RET, error_map


@user_blue.route('/user_info')
@user_login_data
def user_info():
    # 查询用户数据
    user = g.user
    #
    if not user:  # 若没登陆，重定向到首页
        return redirect(url_for("home.index"))

    return render_template("user.html", user=user.to_dict())


# 基本资料
@user_blue.route('/base_info', methods=['POST', 'GET'])
@user_login_data
def base_info():
    user = g.user

    if not user:
        return abort(403)

    if request.method == 'GET':
        return render_template("user_base_info.html", user=user.to_dict())

    # post
    # 获取参数
    signature = request.json.get("signature")  # 个性签名
    nick_name = request.json.get("nick_name")
    gender = request.json.get("gender")

    # 校验参数
    if not all([signature, nick_name, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 默认值
    if gender not in ["MAN", "WOMAN"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 修改用户数据
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 设置头像

@user_blue.route('/pic_info', methods=['GET', 'POST'])
@user_login_data
def pic_info():
    user = g.user
    if not user:
        return abort(403)

    if request.method == "GET":
        return render_template("user_pic_info.html", user=user.to_dict())

    # POST
    # 接收参数
    avatar_file = request.files.get("avatar")
    print('参数：', avatar_file)
    # 获取文件数据
    try:
        file_bytes = avatar_file.read()
        print("二进制", file_bytes)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    #   上传文件到七牛云， 一般会将文件单独管理起来，不同的服务器   业务，文件
    try:
        file_name = file_upload(file_bytes)
        print(file_name)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, error=error_map[RET.THIRDERR])
    print('file_name', file_name)

    # 修改头像链接
    user.avatar_url = file_name

    # json返回  必须返回头像链接
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=user.to_dict())


# 密码修改
@user_blue.route('/pass_info', methods=['GET', 'POST'])
@user_login_data
def pass_info():
    user = g.user
    if not user:
        return abort(403)

    if request.method == 'GET':  # GET 展示页面
        # 直接返回静态页面
        return current_app.send_static_file('news/html/user_pass_info.html')
    print("走到这里了吗？")
    # # POST
    # old_password = request.json.get("old_password")
    # new_password = request.json.get("new_password")
    #
    # # 校验密码
    # if not all([old_password, new_password]):
    #     return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    #
    # # 校验旧密码
    # if not user.check_password(old_password):
    #     return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])
    #
    # # 修改
    # user.password = new_password
    # # user.password_hash = new_password

    # json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


@user_blue.route('/collection')
@user_login_data
def collection():
    user = g.user
    if not user:
        return abort(403)
    return render_template("user_collection.html")


# 新闻发布
@user_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    user = g.user
    if not user:
        return abort(403)

    return render_template("user_news_release.html")

# 我的发布
@user_blue.route('/news_list')
@user_login_data
def news_list():
    user = g.user
    if not user:
        return abort(403)

    return render_template("user_news_list.html")
