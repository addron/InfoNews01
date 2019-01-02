# 管理登陆注册流程
import random
from datetime import datetime

from flask import request, abort, current_app, make_response, session, flash
from flask.json import jsonify

from info import rs, db
from info.utils.constants import IMAGE_CODE_REDIS_EXPIRES, SMS_CODE_REDIS_EXPIRES
from info.libs.captcha.pic_captcha import captcha
from info.utils.models import User
from info.modules.passport import passport_blue

# 注册图片id
from info.utils.response_code import RET, error_map


@passport_blue.route('/get_img_code')
def get_img_code():
    # 获取参数
    img_code_id = request.args.get('img_code_id')

    # 校验
    if not img_code_id:
        return abort(403)  # 拒绝访问

    # 生成图片验证码（图片+文字）  一个什么方法返回三个值
    img_name, img_text, img_bytes = captcha.generate_captcha()

    # 保存验证码文字和图片key
    try:
        rs.set("img_code_id_" + img_code_id, img_text, ex=IMAGE_CODE_REDIS_EXPIRES)
    except BaseException as e:
        current_app.logger.error(e)  # 记录错误信息
        return abort(500)  # 服务器错误

    # 返回图片
    response = make_response(img_bytes)  # type: Response

    # 设置响应头
    response.content_type = 'image/jpeg'
    return response


# 获取短信验证码passport_blue
@passport_blue.route('/get_sms_code', methods=['POST'])
def get_sms_code():
    # 获取参数
    img_code_id = request.json.get("img_code_id")
    img_code = request.json.get("img_code")
    mobile = request.json.get("mobile")

    # 校验参数
    if not all([img_code_id, img_code, mobile]):
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.PARAMERR])  # 参数错误

    # 根据图片key取出验证码文字
    try:
        real_img_code = rs.get("img_code_id_" + img_code_id)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])
    # 数据库查询错误

    # 校验图片验证码（文字）
    if real_img_code != img_code.upper():
        return jsonify(error=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 生成随机短信验证码  "%04d" 是随机四位，不够四位用0补
    rand_num = "%04d" % random.randint(0, 9999)

    # 发送短信
    # response_code = CCP().send_template_sms(mobile, [rand_num, 5], 1)
    # if response_code != 0:  # 发送失败
    #     return jsonify(errno=RET.THIRDERR, errmsg=error_map[RET.THIRDERR])

    current_app.logger.error("短信验证码为： %s" % rand_num)
    # 保存短信验证码  redis
    try:
        rs.set("sms_code_id_" + mobile, rand_num, ex=SMS_CODE_REDIS_EXPIRES)
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])  # 数据库查询错误

    # json返回发送结果  成功
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户注册
@passport_blue.route("/register", methods=['POST'])
def register():
    # 获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")
    sms_code = request.json.get("sms_code")

    # print("mobile：+++"+mobile )
    # print("password：+++"+password )
    # print("sms_code：+++"+sms_code )
    # 校验参数
    if not all([mobile, password, sms_code]):
        return jsonify(errno=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 验证短信验证码  根据mobile提取验证码
    try:
        real_sms_code = rs.get("sms_code_id_" + mobile)
    except BaseException as e:
        current_app.logger.error(e)
        # 返回数据库查询错误
        return jsonify(error=RET.DBERR, errmsg=error_map[RET.DBERR])
    # print(mobile+"不是这个查询吧")
    # 用户数据保存到数据库
    user = User()
    user.mobile = mobile
    user.nick_name = mobile

    # 为方便下面测试，先不加密
    # user.password = password
    user.password_hash = password

    db.session.add(user)
    try:
        db.session.commit()
    except BaseException as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 记录ID
    session['user_id'] = user.id
    # flash("注册成功")
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 用户登陆
@passport_blue.route("/login", methods=["POST"])
def login():
    # 获取参数
    mobile = request.json.get("mobile")
    password = request.json.get("password")

    # 校验参数
    if not all([mobile, password]):
        return jsonify(error=RET.PARAMERR, errmsg=error_map[RET.PARAMERR])

    # 取出用户数据
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except BaseException as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg=error_map[RET.DBERR])

    # 判断用户是否存在
    if not user:
        # 用户不存在或未激活",  RET.USERERR
        return jsonify(error=RET.USERERR, errmsg=error_map[RET.USERERR])

    # 校验密码
    if not user.check_password(password):
        # 密码错误  RET.PWDERR
        return jsonify(errno=RET.PWDERR, errmsg=error_map[RET.PWDERR])

    # 使用session，免密登陆
    session['user_id'] = user.id

    # # 记录最后登录时间  使用sqlalchemy自动提交机制
    user.last_login = datetime.now()
    # flash("登陆成功")
    #
    # return jsonify(error=RET.OK, errmsg=error_map[RET.OK])
    return jsonify(errno=RET.OK, errmsg=error_map[RET.OK])


# 退出登陆
@passport_blue.route("/logout")
def logout():
    # 删除session中的user_id
    session.pop("user_id", None)
    # flash("已退出")
    return jsonify(error=RET.OK, errmsg=error_map[RET.OK])
