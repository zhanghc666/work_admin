from meiduo_mall.libs.yuntongxun.sms import CCP
from verifications import constants
from celery_tasks.main import celery_app


@celery_app.task(name='send_sms_code')  # 用装饰器装饰普通函数就变成了celery的任务
def send_sms_code(mobile, sms_code):
    """
    发短信的任务
    :param mobile: 要收短信的手机号
    :param sms_code: 验证码
    """
    # CCP().send_template_sms(接收短信的手机号, [短信验证码, 提示用户的过期时间单位:分钟], 模板id)
    CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60], 1)


