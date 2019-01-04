from flask import render_template, current_app, abort, g, jsonify, request

from info import db
from info.modules.news import news_blue
from info.utils.common import user_login_data
from info.utils.models import News, Comment
from info.utils.response_code import RET, error_map


# 新闻详情
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

    # 查询用户
    # user_login_data()
    # user = g.user.to_dict() if g.user else None
    news.clicks += 1

    user = g.user
    # print("user有值么：", user.avatar_url)
    is_collected = False  # 记录收藏情况
    if user:
        # 当前用户是否收藏了该新闻
        if news in user.collection_news:
            is_collected = True

    # 查询该新闻所有评论
    comments = []
    try:
        comments = news.comments.order_by(Comment.create_time.desc()).all()
    except BaseException as e:
        current_app.logger.error(e)

    comment_list = []
    for comment in comments:
        comment_dict = comment.to_dict()

        # 查询评论是否被当前用户点过赞
        is_like = False
        if user:
            if comment in user.like_comments:
                is_like = True

        comment_dict['is_like'] = is_like
        comment_list.append(comment_dict)

    is_followed = False  # 关注
    if news.user and user:  # 目前新闻有作者，且有用户登陆
        # 查询作者是否被当前用户关注
        if news.user in user.followers:
            is_followed = True

    return render_template("news/detail.html", news=news.to_dict(), rank_list=rank_list, user=user.to_dict(),
                           is_collected=is_collected, comments=comment_list, is_followed=is_followed)


# 新闻收藏
@news_blue.route('/news_collect', methods=['POST'])
@user_login_data
def news_collect():
    user = g.user
    if not user:  # 未登录
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    action = request.json.get("action")
    news_id = request.json.get("news_id")

    # 校验参数
    if not all([action, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    if action not in ["collect", "cancel_collect"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取新闻数据
    try:
        news_id = int(news_id)
        news = News.query.get(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据action建立关系
    if action == "collect":  # 收藏
        user.collection_news.append(news)
    else:  # 取消
        user.collection_news.remove(news)

    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 新闻评论
@news_blue.route('/news_comment', methods=['POST'])
@user_login_data
def news_comment():
    user = g.user
    if not user:  # 未登录
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    comment_content = request.json.get("comment")
    parent_id = request.json.get("parent_id")
    news_id = request.json.get("news_id")

    # 校验参数及转换
    if not all([comment_content, news_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])
    try:
        news_id = int(news_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 生成一条评论记录
    comment = Comment()
    comment.content = comment_content
    comment.news_id = news_id
    comment.user_id = user.id

    if parent_id:  # 有子评论
        try:
            parent_id = int(parent_id)
            comment.parent_id = parent_id
        except BaseException as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    db.session.add(comment)
    # 为了生成主键，必须手动提交
    try:
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # json返回结果  必须返回该评论的id
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK], data=comment.to_dict())


# 评论点赞
@news_blue.route('/comment_like', methods=['POST'])
@user_login_data
def comment_like():
    user = g.user
    if not user:  # 未登陆
        return jsonify(errno=RET.SESSIONERR, errmsg=error_map[RET.SESSIONERR])

    # 获取参数
    action = request.json.get("action")
    comment_id = request.json.get("comment_id")

    # 校验
    if not all([action, comment_id]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    if action not in ["add", "remove"]:
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 获取评论数据
    try:
        comment_id = int(comment_id)
        comment = Comment.query.get(comment_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 根据action建立/解除点赞
    if action == "add":
        user.like_comments.append(comment)
        # 点赞书加１
        comment.like_count += 1
    else:
        user.like_comments.remove(comment)
        comment.like_count -= 1

    # json返回结果
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])
