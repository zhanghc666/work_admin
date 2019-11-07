
from django.shortcuts import render
from django.views import View
from meiduo_mall.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.libs.yuntongxun.sms import CCP
from random import randint
from . import constants
from celery_tasks.sms.tasks import send_sms_code

import logging
logger = logging.getLogger('django')

# Create your views here.

class ImageCodeView(View):
    """图片验证码"""
    def get(self, request, uuid):
        # 1.生成图形验证码 SDK
        # name:随机标识, text:图形验证码内容, image_code: bytes类型的图形验证码图片数据
        name, text, image_code = captcha.generate_captcha()
        # 2.创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')

        # 3.存储图形验证码内容到redis中
        # setex(key, 过期时间, value)
        redis_conn.setex(uuid, 300, text)

        # 4.把图形验证码响应img标签
        return http.HttpResponse(image_code, content_type='image/png')


class SMSCodeView(View):
    """短信验证码"""
    def get(self, request, mobile):
        # 创建redis链接对象
        redis_conn = get_redis_connection('verify_codes')

        # 发短信前先获取当前手机号60s内是否发送短信标识
        send_flag = redis_conn.get('send_flag_%s' % mobile)

        # 判断是否已经获取到标识，如果获取到提前响应
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '频繁发送短信'})



        # 1.接收: mobile, image_code_client, uuid
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')


        # 2.校验
        if all([image_code_client, uuid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')


        # 2.1 创建redis连接对象
        redis_conn = get_redis_connection('verify_codes')

        # 获取redis中的图形验证码
        # 从redis中获取出来的所有数据都是bytes类型 str, list, dict, set
        image_code_server_bytes = redis_conn.get(uuid)

        # 设置图形验证码一次性  ##############
        redis_conn.delete(uuid)

        # 判断图形验证码是否已过期
        if image_code_server_bytes is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码已过期'})

        # 将redis中取出的图形验证码转换成str
        image_code_server = image_code_server_bytes.decode()

        # 判断图形验证码是否正确
        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码添加错误'})

        # 生成短信验证码
        sms_code = '%06d' % randint(0, 999999)
        logger.info(sms_code)


        # 3.发送短信验证码(容联云通讯)
        # CCP().send_template_sms(接收短信的手机号, [短信验证码, 提示用户的过期时间单位:分钟], 模板id)
        # CCP().send_template_sms(mobile, [sms_code, 5],1)
        # CCP().send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES // 60],1)
        # send_sms_code(mobile, sms_code)
        # 生产celery任务,本质只是将当前函数的引用向redis中添加
        send_sms_code.delay(mobile, sms_code)

        # 创建redis管道  #############
        pl = redis_conn.pipeline()

        # 存储短信验证码到redis
        # redis_conn.setex('sms_code_%s' % mobile, 300, sms_code)
        # redis_conn.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex('sms_code_%s' % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)

        # 对当前发过短信的手机号存储一个有效期60s的短信标识
        # redis_conn.setex('send_flag_%s' % mobile, constants.SMS_CODE_SEND_FLAG_REDIS_EXPIRES, 1)
        pl.setex('send_flag_%s' % mobile, constants.SMS_CODE_SEND_FLAG_REDIS_EXPIRES, 1)

        # 执行管道  ###########
        pl.execute()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


