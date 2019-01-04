# from flask import session
import datetime
import random

from flask_script import Manager
from flask_migrate import MigrateCommand
from info import create_app

# 创建web应用
app = create_app("dev")

# 创建管理器
mgr = Manager(app)

# 使用管理器生成迁移命令
mgr.add_command("mc", MigrateCommand)


@mgr.option("-u", dest="username")  # python main.py create_superuser -u admin -p 123456
@mgr.option("-p", dest="password")  # 将有参函数变为命令
def create_superuser(username, password):
    if not all([username, password]):
        app.logger.error("添加管理员失败: 参数不足")
        return

    from info.utils.models import User
    from info import db
    # 添加管理员用户  is_admin true
    user = User()
    user.mobile = username
    user.password = password
    user.nick_name = username
    user.is_admin = True

    db.session.add(user)
    try:
        db.session.commit()
    except BaseException as e:
        app.logger.error("添加管理员失败：%s" % e)
        db.session.rollback()
        return
    app.logger.info("添加管理员成功")


# @mgr.command  # 无参 将无参函数转为命令
# def demo():
#     print("demo1")

# 添加测试数据，用户
@mgr.command
def add_test_users():
    # 添加测试用户
    from info import db
    from info.utils.models import User

    users = []
    now = datetime.datetime.now()
    for num in range(0, 10000):
        try:
            user = User()
            user.nick_name = "%010d" % num
            user.password_hash = "pbkdf2:sha256:50000$SgZPAbEj$a253b9220b7a916e03bf27119d401c48ff4a1c81d7e00644e0aaf6f3a8c55829"
            user.create_time = now - datetime.timedelta(seconds=random.randint(0, 2678400))
            users.append(user)

        except Exception as e:
            print(e)

    db.session.add_all(users)
    db.session.commit()
    print('OK')


if __name__ == '__main__':
    mgr.run()
