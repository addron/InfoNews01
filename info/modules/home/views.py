from info.utils.constants import HOME_PAGE_MAX_NEWS
from info.modules.home import home_blue
from flask import render_template, current_app, session, abort, request,jsonify

# 使用蓝图来注册路由
from info.utils.models import User, News, Category
from info.utils.response_code import RET, error_map


@home_blue.route('/')
def index():
    # 判断用户是否已登陆
    user_id = session.get("user_id")

    user = None

    # 若登陆，查出相关信息
    if user_id:
        try:
            user = User.query.get(user_id)
        except BaseException as e:
            current_app.logger.error(e)
    user = user.to_dict() if user else None

    # 点击量前10的新闻
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except BaseException as e:
        current_app.logger.error(e)

    rank_list = [news.to_basic_dict() for news in rank_list]

    # 查询所有分类数据
    try:
        categories = Category.query.all()
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)

    return render_template("index.html", user=user, rank_list=rank_list,categories=categories)


# 设置网站图标 (浏览器会自动向网站发起/favicon.ico请求, 后端只需要实现该路由,并返回图片即可)
@home_blue.route('/favicon.ico')
def favico():
    # flask中封装了语法send_static_file
    # 可以获取静态文件的内容, 封装为响应对象, 并根据内容设置content-type
    response = current_app.send_static_file("news/favicon.ico")  # 相对路径基于static文件夹

    return response

# 获取新闻列表
@home_blue.route('/get_news_list')
def get_news_list():
    # 获取参数  cid 分类id
    cid = request.args.get("cid")
    cur_page = request.args.get("cur_page") # 页数
    per_count = request.args.get("per_count",HOME_PAGE_MAX_NEWS) # 次数

    # 校验参数
    if not all([cid,cur_page,per_count]):
       # 导入了from flask.json import jsonify   或许有错

        return jsonify(error=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    # 格式转换
    try:
        cid = int(cid)
        cur_page = int(cur_page)
        per_count = int(per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(error=RET.PARAMERR,errmsg=error_map[RET.PARAMERR])

    filter_list = []

    # 把 条件放入列表，可以节省sql
    if cid != 1:  # 不是“最新”
        filter_list.append(News.category_id == cid)

    try:
        pn = News.query.filter(*filter_list).order_by(News.create_time.desc()).paginate(cur_page, per_count)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 数据包装成json返回
    data = {
        "new_list":[news.to_basic_dict() for news in pn.items],
        "total_pape":pn.pages
    }
    return jsonify(error=RET.OK,errmsg=error_map[RET.OK])








