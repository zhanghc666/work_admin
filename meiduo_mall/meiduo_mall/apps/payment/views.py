from django.shortcuts import render
from django import http
from alipay import AliPay
from django.conf import settings
import os

from meiduo_mall.utils.views import LoginRequiredView
from orders.models import OrderInfo
from meiduo_mall.utils.response_code import RETCODE
from .models import Payment


class PaymentURLView(LoginRequiredView):
    """拼接支付宝登录url"""

    def get(self, request, order_id):
        user = request.user
        # 1.校验
        try:
            order = OrderInfo.objects.get(order_id=order_id, user=user, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'])
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')

        # 2.创建支付SDK中的alipay实例对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # /Users/chao/Desktop/meiduo_31/meiduo/meiduo/apps/payment/keys/app_private_key.pem
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False, 沙箱环境True
        )
        # 3. 调用SDK中的api_alipay_trade_page_pay 得到支付登录url的查询参数部分
        order_string = alipay.api_alipay_trade_page_pay(
            out_trade_no=order_id,  # 美多订单编号
            total_amount=str(order.total_amount),  # 支付金额要转换成str
            subject='美多商城:%s' % order_id,
            return_url=settings.ALIPAY_RETURN_URL,
        )

        # 4. 拼接完整的支付宝登录url
        # 电脑网站支付，需要跳转到
        # 真实支付URL:    https://openapi.alipay.com/gateway.do? + order_string
        # 沙箱环境支付URL:    https://openapi.alipaydev.com/gateway.do? + order_string
        alipay_url = settings.ALIPAY_URL + '?' + order_string
        # 5. 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'alipay_url': alipay_url})


class PaymentStatusView(LoginRequiredView):
    """校验支付结果"""
    def get(self, request):

        # 1.接收查询参数
        query_dict = request.GET

        # 2.将QueryDict类型转换成dict
        data = query_dict.dict()

        # 3.将参数中sign 加密部分移除
        sign = data.pop('sign')

        # 4. 调用Alipay SDK中 verify方法进行校验
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            app_notify_url=None,  # 默认回调url
            # /Users/chao/Desktop/meiduo_31/meiduo/meiduo/apps/payment/keys/app_private_key.pem
            app_private_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'keys/app_private_key.pem'),
            # 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
            alipay_public_key_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                'keys/alipay_public_key.pem'),
            sign_type="RSA2",  # RSA 或者 RSA2
            debug=settings.ALIPAY_DEBUG  # 默认False, 沙箱环境True
        )

        if alipay.verify(data, sign):
            # 如果校验成功
            # 获取美多订单编号
            order_id = data.get('out_trade_no')
            # 获取支付宝交易号
            trade_id = data.get('trade_no')
            # 5. 保存支付结果,将order_id和支付宝交易号保存到一起
            try:
                Payment.objects.get(trade_id=trade_id)
            except Payment.DoesNotExist:
                payment = Payment.objects.create(
                    order_id=order_id,
                    trade_id=trade_id
                )
                # 6. 修改已支付订单的状态
                OrderInfo.objects.filter(order_id=order_id, status=OrderInfo.ORDER_STATUS_ENUM['UNPAID'],
                                         user=request.user).update(status=OrderInfo.ORDER_STATUS_ENUM['UNCOMMENT'])
            return render(request, 'pay_success.html', {'trade_id': trade_id})
        else:
            return http.HttpResponseBadRequest('非法请求')