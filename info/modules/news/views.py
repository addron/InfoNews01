from flask import render_template, current_app, abort, g

from info.modules.news import news_blue


# 使用蓝图来注册路由
from info.utils.common import user_login_data
from info.utils.models import News



@news_blue.route('/<int:news_id>')
@user_login_data  # news_tetail = user_login_data(news_detail)
def news_detail(news_id):
    # print(news_id)
    try:
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return abort(500)
    # 查询排行前10的新闻
    rank_list = []
    try:
        rank_list = News.query.order_by(News.clicks.desc()).limit(10).all()
    except BaseException as e:
        current_app.logger.error(e)

    rank_list = [news.to_dict() for news in rank_list]

    # # 查询用户
    # user_login_data()
    # user = g.user.to_dict() if g.user else None
    news.clicks += 1
    user = g.user

    return render_template("detail.html",news=news.to_dict(),rank_list=rank_list,user=user)

