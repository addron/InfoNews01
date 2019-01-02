# 定义过滤器
import functools
from flask import session, current_app, g

from info.utils.models import User


def func_index_convert(index):  # index = 4

    index_dict = {1: "first", 2: "second", 3: "third"}

    return index_dict.get(index, "")


# 查询用户数据
def user_login_data(f):
    # 裝飾器
    #  如果使用闭包函数的名称来构建函数标记，会出现标记冲突
    @functools.wraps(f)  # 该装饰器可以让被装饰的函数使用指定函数的名称，
    def wrappers(*args, **kwargs):

        # 判断用户是否登陆
        user_id = session.get("user_id")
        user = None
        if user_id:  # 已登录
            try:
                user = User.query.get(user_id)
            except BaseException as e:
                current_app.logger.error(e)
        g.user = user
        return f(*args, **kwargs)

    return wrappers


# 上传到七牛云
def file_upload(data):
    """
    上传文件到七牛云
    :param data:  要上传的文件
    :return: 保存到七牛云的文件名
    """
    import qiniu
    access_key = "kJ8wVO7lmFGsdvtI5M7eQDEJ1eT3Vrygb4SmR00E"
    secret_key = "rGwHyAvnlLK7rU4htRpNYzpuz0OHJKzX2O1LWTNl"
    bucket_name = "infonews22"  # 空间名称

    q = qiniu.Auth(access_key, secret_key)
    key = None  # 设置文件名, 如果为None, 就会生成随机名称

    token = q.upload_token(bucket_name)

    ret, info = qiniu.put_data(token, key, data)
    if ret is not None:
        return ret.get('key')  # 文件名
    else:
        raise BaseException(info)  # error message in info

    # import qiniu
    # access_key = "kJ8wVO7lmFGsdvtI5M7eQDEJ1eT3Vrygb4SmR00E"
    # secret_key = "rGwHyAvnlLK7rU4htRpNYzpuz0OHJKzX2O1LWTNl"
    # bucket_name = "infonews22"  # 空间名称
    #
    # q = qiniu.Auth(access_key, secret_key)
    # key = None  # 设置文件名，如果为None，就会随机取名
    #
    # token = q.upload_token(bucket_name)
    #
    # ret, info = qiniu.put_data(token, key, data)
    #
    # if ret is not None:
    #     return ret.get('key') # 文件名
    # else:
    #     raise BaseException(info) # 异常信息
