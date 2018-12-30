from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

from info import db
from info.utils import constants


# 表基类    为每个表添加共同的字段: 记录的创建时间与更新时间
class BaseModel(object):
    create_time = db.Column(db.DateTime, default=datetime.now)  # 记录的创建时间  default参数用于设置字段的默认值, 可以为基本类型/函数引用
    update_time = db.Column(db.DateTime, default=datetime.now,
                            onupdate=datetime.now)  # 记录的更新时间   当记录发生数据更新时, 字段会修改为onupdate参数的值


# 用户表
class User(BaseModel, db.Model):
    __tablename__ = "info_user"

    id = db.Column(db.Integer, primary_key=True)  # 用户编号
    nick_name = db.Column(db.String(32), unique=True, nullable=False)  # 用户昵称
    password_hash = db.Column(db.String(128), nullable=False)  # 加密的密码
    mobile = db.Column(db.String(11), unique=True, nullable=False)  # 手机号
    avatar_url = db.Column(db.String(256))  # 用户头像路径
    last_login = db.Column(db.DateTime, default=datetime.now)  # 最后一次登录时间
    is_admin = db.Column(db.Boolean, default=False)
    signature = db.Column(db.String(512))  # 用户签名
    gender = db.Column(  # 订单的状态
        db.Enum(
            "MAN",  # 男
            "WOMAN"  # 女
        ),
        default="MAN")

    # 当前用户收藏的所有新闻
    collection_news = db.relationship("News", secondary="info_user_collection", lazy="dynamic")  # 用户收藏的新闻
    # 当前用户点赞的所有评论
    like_comments = db.relationship("Comment", secondary="info_comment_like", lazy="dynamic")

    # 用户所有的粉丝    自关联多对多关系属性,需要设置primaryjoin和secondaryjoin
    followers = db.relationship('User',
                                secondary="info_user_fans",
                                # 该关系属性根据哪个外键查, primaryjoin就设置哪个外键, 另一个设置为secondaryjoin
                                primaryjoin="UserFollow.followed_id==User.id",
                                secondaryjoin="UserFollow.follower_id==User.id",
                                backref=db.backref('followed', lazy='dynamic'),
                                lazy='dynamic')

    # 当前用户所发布的新闻
    news_list = db.relationship('News', backref='user', lazy='dynamic')

    # 计算型属性 ： 对属性赋值/取值时， 会调用对应的方法, 可以在方法中封装一些处理

    @property
    def password(self):
        raise AttributeError("该属性不可取值")

    @password.setter
    def password(self, value):
        # 封装加密过程

        self.password_hash = generate_password_hash(value)

    def check_password(self, password):
        """

        :param password: 用户输入的明文
        :return:  true表示校验成功
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self):  # 将模型中的数据转存到了字典中, 并且封装了数据的判断和格式转换
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "avatar_url": constants.QINIU_DOMIN_PREFIX + self.avatar_url if self.avatar_url else "",
            "mobile": self.mobile,
            "gender": self.gender if self.gender else "MAN",
            "signature": self.signature if self.signature else "",
            "followers_count": self.followers.count(),
            "news_count": self.news_list.count()
        }
        return resp_dict

    def to_admin_dict(self):
        resp_dict = {
            "id": self.id,
            "nick_name": self.nick_name,
            "mobile": self.mobile,
            "register": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": self.last_login.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return resp_dict


# 新闻表
class News(BaseModel, db.Model):
    __tablename__ = "info_news"

    id = db.Column(db.Integer, primary_key=True)  # 新闻编号
    title = db.Column(db.String(256), nullable=False)  # 新闻标题
    source = db.Column(db.String(64), nullable=False)  # 新闻来源
    digest = db.Column(db.String(512), nullable=False)  # 新闻摘要
    content = db.Column(db.Text, nullable=False)  # 新闻内容
    clicks = db.Column(db.Integer, default=0)  # 浏览量
    index_image_url = db.Column(db.String(256))  # 新闻列表图片路径
    category_id = db.Column(db.Integer, db.ForeignKey("info_category.id"))
    user_id = db.Column(db.Integer, db.ForeignKey("info_user.id"))  # 当前新闻的作者id
    status = db.Column(db.Integer, default=0)  # 当前新闻状态 如果为0代表审核通过，1代表审核中，-1代表审核不通过
    reason = db.Column(db.String(256))  # 未通过原因，status = -1 的时候使用
    # 当前新闻的所有评论
    comments = db.relationship("Comment", lazy="dynamic")

    def to_review_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "status": self.status,
            "reason": self.reason if self.reason else ""
        }
        return resp_dict

    def to_basic_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "index_image_url": self.index_image_url,
            "clicks": self.clicks,
        }
        return resp_dict

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "digest": self.digest,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "comments_count": self.comments.count(),
            "clicks": self.clicks,
            "category": self.category.to_dict(),
            "index_image_url": self.index_image_url if self.index_image_url else "",
            "author": self.user.to_dict() if self.user else None
        }
        return resp_dict


# 分类表
class Category(BaseModel, db.Model):
    __tablename__ = "info_category"

    id = db.Column(db.Integer, primary_key=True)  # 分类编号
    name = db.Column(db.String(64), nullable=False)  # 分类名
    news_list = db.relationship('News', backref='category', lazy='dynamic')

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "name": self.name
        }
        return resp_dict


# 评论表
class Comment(BaseModel, db.Model):
    __tablename__ = "info_comment"

    id = db.Column(db.Integer, primary_key=True)  # 评论编号
    user_id = db.Column(db.Integer, db.ForeignKey("info_user.id"), nullable=False)  # 用户id
    news_id = db.Column(db.Integer, db.ForeignKey("info_news.id"), nullable=False)  # 新闻id
    content = db.Column(db.Text, nullable=False)  # 评论内容
    parent_id = db.Column(db.Integer, db.ForeignKey("info_comment.id"))  # 父评论id
    # 自关联多对一关系属性, 需要设置remote_side=[主键名]
    # parent = db.relationship("Comment", remote_side=[id])
    children = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]))
    like_count = db.Column(db.Integer, default=0)  # 点赞条数

    def to_dict(self):
        resp_dict = {
            "id": self.id,
            "create_time": self.create_time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": self.content,
            "parent": self.parent.to_dict() if self.parent else None,
            "user": User.query.get(self.user_id).to_dict(),
            "news_id": self.news_id,
            "like_count": self.like_count
        }
        return resp_dict


# 新闻收藏表      记录用户与其收藏新闻的多对多的关系
class UserCollection(db.Model):
    __tablename__ = "info_user_collection"
    user_id = db.Column(db.Integer, db.ForeignKey("info_user.id"), primary_key=True)  # 用户id
    news_id = db.Column(db.Integer, db.ForeignKey("info_news.id"), primary_key=True)  # 新闻id


# 用户关注表      记录作者与粉丝的多对多的关系
class UserFollow(db.Model):
    __tablename__ = "info_user_fans"
    follower_id = db.Column(db.Integer, db.ForeignKey("info_user.id"), primary_key=True)  # 粉丝id
    followed_id = db.Column(db.Integer, db.ForeignKey("info_user.id"), primary_key=True)  # 作者id


# 评论点赞表     记录用户与评论的多对多的关系
class CommentLike(BaseModel, db.Model):
    __tablename__ = "info_comment_like"
    comment_id = db.Column("comment_id", db.Integer, db.ForeignKey("info_comment.id"), primary_key=True)  # 评论编号
    user_id = db.Column("user_id", db.Integer, db.ForeignKey("info_user.id"), primary_key=True)  # 用户编号
