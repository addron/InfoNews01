import logging
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_migrate import Migrate
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from redis import Redis

from config import config_dict

# 定义全局变量, 记录数据库连接对象, 以便其他文件可以使用
db = None  # type: SQLAlchemy
rs = None  # type: Redis


# 封装应用的创建过程  工厂函数: 让外界提供物料, 在函数内部封装对象的创建过程
def create_app(config_type):
    config_class = config_dict[config_type]

    # 创建web应用
    app = Flask(__name__)

    # 从对象中加载配置
    app.config.from_object(config_class)

    # 声明全局变量
    global db, rs

    # 创建msql连接对象
    db = SQLAlchemy(app)
    # 创建redis连接对象
    rs = Redis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, decode_responses=True)

    # 初始化session存储对象
    Session(app)

    # 初始化迁移器
    Migrate(app, db)

    # 注册蓝图对象
    # 为了避免导入错误, 对于只使用一次的内容, 在使用前才导入
    from info.modules.home import home_blue
    app.register_blueprint(home_blue)
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)

    # 项目关联模型文件   import *语法不能在函数/方法中使用
    # from info import models

    import info.utils.models

    # 配置日志
    setup_log(config_class.LOGLEVEL)
    from info.utils.common import func_index_convert
    # 添加过滤器
    app.add_template_filter(func_index_convert, "index_convert")

    return app


# 配置日志文件(将flask内置的日志和自定义的日志保存到文件中)
def setup_log(log_level):
    # 设置日志的记录等级

    logging.basicConfig(level=log_level)  # 调试dubug等级

    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件的个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(levelname)s %(pathname)s:%(lineno)d %(message)s')

    # 为刚刚创建的日志记录器设置日志记录格式，
    file_log_handler.setFormatter(formatter)

    # 为全局的日志工具对象 添加日志记录器
    logging.getLogger().addHandler(file_log_handler)
