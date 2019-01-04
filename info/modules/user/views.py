from flask import render_template, g, redirect, url_for, abort, request, jsonify, current_app

from info import db
from info.modules.user import user_blue
from info.utils.common import user_login_data, file_upload
from info.utils.constants import USER_COLLECTION_MAX_NEWS, QINIU_DOMIN_PREFIX
from info.utils.models import UserCollection, Category, News
from info.utils.response_code import RET, error_map


@user_blue.route('/user_info')
@user_login_data
def user_info():
    # 查询用户数据
    user = g.user
    #
    if not user:  # 若没登陆，重定向到首页
        return redirect(url_for("home.index"))

    return render_template("news/user.html", user=user.to_dict())


# 基本资料
@user_blue.route('/base_info', methods=['POST', 'GET'])
@user_login_data
def base_info():
    user = g.user

    if not user:
        return abort(403)

    if request.method == 'GET':
        return render_template("news/user_base_info.html", user=user.to_dict())

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
        return render_template("news/user_pic_info.html", user=user.to_dict())

    # POST
    # 接收参数
    avatar_file = request.files.get("avatar")
    # print('参数：', avatar_file)
    # 获取文件数据
    try:
        file_bytes = avatar_file.read()
        # print("二进制", file_bytes)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    #   上传文件到七牛云， 一般会将文件单独管理起来，不同的服务器   业务，文件
    try:
        file_name = file_upload(file_bytes)
        # print(file_name)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, error=error_map[RET.THIRDERR])
    # print('file_name', file_name)

    # 修改头像链接
    user.avatar_url = file_name
    print(user.avatar_url)
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
    # print("走到这里了吗？")
    # POST
    old_password = request.json.get("old_password")
    new_password = request.json.get("new_password")

    # 校验密码
    if not all([old_password, new_password]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 校验旧密码
    if not user.check_password(old_password):
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 修改
    user.password = new_password
    # user.password_hash = new_password

    # json返回
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 个人中心我的收藏
@user_blue.route('/collection')
@user_login_data
def collection():
    user = g.user
    if not user:
        return abort(403)

    p = request.args.get("p", 1)  # p是页数，默认为1

    # 校验
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)
    # 查询，分页查找，收藏时间倒叙
    try:
        pn = user.collection_news.order_by(UserCollection.create_time.desc()).paginate(p, USER_COLLECTION_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    # 包装成json
    data = {
        "news_list": [news.to_dict() for news in pn.items],
        "total_page": pn.pages,
        "cur_page": pn.page
    }

    return render_template("news/user_collection.html", data=data)


# 新闻发布  分类下拉框需要渲染
@user_blue.route('/news_release', methods=['GET', 'POST'])
@user_login_data
def news_release():
    user = g.user
    if not user:
        return abort(403)

    if request.method == 'GET':  # 展示页面
        try:
            categories = Category.query.filter(Category.id != 1).all()
        except BaseException as e:
            current_app.logger.error(e)
            return abort(500)

        # 传入模板
        return render_template("news/user_news_release.html", categories=categories)

    # post 提交资料
    # 获取参数
    title = request.form.get("title")  # 标题
    category_id = request.form.get("category_id")  # 分类
    digest = request.form.get("digest")  # 摘要
    content = request.form.get("content")  # 内容
    img_file = request.files.get("index_image")  # 图片
    # 校验参数
    if not all([title, category_id, digest, content, img_file]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    try:
        category_id = int(category_id)
    except BaseException as e:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 生成记录
    news = News()
    news.title = title
    news.category_id = category_id
    news.digest = digest
    news.content = content

    # 文件需要上传
    try:
        img_bytes = img_file.read()
        # 上传文件 file_ipload 返回一个文件名
        file_name = file_upload(img_bytes)
        news.index_image_url = QINIU_DOMIN_PREFIX + file_name
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    # 其他数据
    news.source = '个人中心'  # 新闻来源
    news.user_id = user.id  # 作者id
    news.status = 1  # 审核中  0 通过   -1 不通过

    # 添加到事物,有自动提交
    db.session.add(news)

    # 返回json
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 我的发布
@user_blue.route('/news_list')
@user_login_data
def news_list():
    user = g.user
    if not user:
        return abort(403)

    # 获取参数
    p = request.args.get('p', 1)

    # 校验参数
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)

    # 查询当前用户发布的新闻
    try:
        pn = user.news_list.order_by(News.create_time.desc()).paginate(p, USER_COLLECTION_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    # data
    data = {
        "news_list": [news.to_dict() for news in pn.items],  # 新闻列表
        "total_page": pn.pages,  # 总页数
        "cur_page": pn.page  # 当前页数
    }

    return render_template("news/user_news_list.html", data=data)


# 我的关注
@user_blue.route('/user_follow')
@user_login_data
def user_follow():
    user = g.user
    if not user:
        return abort(403)

    # 获取参数
    p = request.args.get("p", 1)

    # 校验参数
    try:
        p = int(p)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(403)

    # 查询当前用户关注的作者   分页查询
    try:
        pn = user.followers
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    # 查询当前用户关注的作者  followes 作者关注的用户  分页查询
    try:
        pn = user.followed.paginate(p, USER_COLLECTION_MAX_NEWS)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    data = {
        "author_list": [user.to_dict() for user in pn.items],
        "total_page": pn.pages,
        "cur_page": pn.page
    }

    # 数据传入模板渲染
    return render_template("news/user_follow.html", data=data)