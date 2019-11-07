from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django import http
from django.contrib.auth import login
import re
from django_redis import get_redis_connection
from QQLoginTool.QQtool import OAuthQQ


from meiduo_mall.utils.response_code import RETCODE
from .models import OAuthQQUser, OAuthWEIBOUser
from users.models import User
from .utils import generate_openid_signature, generate_origin_openid
from carts.utils import merge_cart_cookie_to_redis
from .sinaweibopy3 import APIClient

# Create your views here.


class OAuthQQURLView(View):
    """拼接QQ登录url"""
    def get(self, request):
        # 1.获取查询参数
        next = request.GET.get('next') or '/'

        # 2.创建QQ登录工具对象
        # oauth = OAuthQQ(client_id='101518219',
        #                 client_secret='418d84ebdc7241efb79536886ae95224',
        #                 redirect_url='http://www.meiduo.site:8000/oauth_callback',
        #                 state=next)

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 3.调用QQ登录工具对象中的get_qq_url方法得到拼接好的url
        login_url = oauth.get_qq_url()

        # 4.响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url':login_url})


class OAuthQQView(View):
    """QQ扫玛后回调函数处理"""
    def get(self, request):
        # 1.获取查询参数中的code
        code = request.GET.get('code')
        # 2.校验
        if code is None:
            return http.HttpResponseForbidden('缺少code')
        # 3.创建QQ登录工具对象
        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=next)

        # 4.调用QQ登录工具对象get_access_token
        access_token = oauth.get_access_token(code)

        # 5.调用QQ登录工具对象get_open_id
        openid = oauth.get_open_id(access_token)

        # 6.以openid字符串查询oauth_qq表
        try:
            auth_qq_model = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 6.1如果没有查询到，说明此openid没有和美多用户关联，返回一个关联绑定页面

            # 此处的openid需要加密处理
            openid = generate_openid_signature(openid)
            context = {'openid':openid}
            return render(request, 'oauth_callback.html', context)

        else:
            # 6.2 查询到了，说明此openid已绑定美多用户,代表登录成功
            # 如果已绑定代表登录成功,状态保持及重定向来源
            user = auth_qq_model.user  # 通过外键获取openid关联user模型对象
            login(request, user)  # 状态保持
            response = redirect(request.GET.get('state'))
            response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
            # 合并购物车数据
            merge_cart_cookie_to_redis(request, response)
            return response


    def post(self, request):
        # 1.接收表单数据mobile,password,sms_code,openid
        query_dict = request.POST
        mobile = query_dict.get('mobile')
        password = query_dict.get('password')
        sms_code = query_dict.get('sms_code')
        openid = query_dict.get('openid')


        # 2.校验
        if all([mobile, password, sms_code, openid]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号')

        if not re.match('^[0-9A-Za-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        # 对openid进行解密,将原始openid存储到表中
        openid = generate_origin_openid(openid)
        if openid is None:
            return http.HttpResponseForbidden('openid无效')

        # 获取redis中的短信验证码
        redis_conn = get_redis_connection('verify_codes')
        sms_code_server_bytes = redis_conn.get('sms_code_%s' % mobile)
        # 让短信验证码成为一次性的
        redis_conn.delete('sms_code_%s' % mobile)
        # 判断短信验证码是否过期
        if sms_code_server_bytes is None:
            return http.HttpResponseForbidden('短信验证码已过期')
        # 转换reids中短信验证码类型
        sms_code_server = sms_code_server_bytes.decode()
        # 判断用户验证码是否正确
        if sms_code != sms_code_server:
            return http.HttpResponseForbidden('验证码输入有误')

        # 以mobile字典查询user表，如果查询到就认为ie是老用户，直接用openid和老用户绑定
        try:
            user = User.objects.get(mobile=mobile)
            if user.check_password(password) is False:
                return http.HttpResponseForbidden('老用户密码错误')
        except User.DoesNotExist:
            # 如果是美多新用户，就创建一个新用户和openid绑定
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)


        # 3.openid绑定user
        OAuthQQUser.objects.create(openid=openid, user=user)

        # 状态保持
        login(request, user)
        response = redirect(request.GET.get('state'))
        # 向cookie中存储username
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)

        # 合并购物车数据
        merge_cart_cookie_to_redis(request,response)
        return response

class OAuthWeiboURLView(View):
    """拼接weibo登录url"""
    def get(self, request):

        # 1.获取查询参数 next
        next = request.GET.get('next') or '/'

        # 2. 创建weibo登录工具对象

        client = APIClient(app_key=settings.WEIBO_CLIENT_ID,
                        app_secret=settings.WEIBO_CLIENT_SECRET,
                        redirect_uri=settings.WEIBO_REDIRECT_URI,
                        )

        # 3. 调用weibo登录工具对象中的get_authorize_url方法得到拼接好的url
        # login_url = client.get_authorize_url(state=next) #############
        login_url = client.get_authorize_url()
        # 4. 响应json
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})

class OAuthWeiboView(View):
    """微博授权登录后回调处理"""

    def get(self, request):
        # 1.获取查询参数中的code
        code = request.GET.get('code')

        # 2.校验
        if code is None:
            return http.HttpResponseForbidden('缺少code')

        # 3. 创建微博登录工具对象
        client = APIClient(app_key=settings.WEIBO_CLIENT_ID,
                           app_secret=settings.WEIBO_CLIENT_SECRET,
                           redirect_uri=settings.WEIBO_REDIRECT_URI,
                           )

        # 4. 调用微博登录工具对象 request_access_token
        result = client.request_access_token(code)
        # access_token = result.access_token
        # 5. 获得uid ,就是result中携带的键
        uid = result.uid

        # 6. 以openid字符查询 oauth_qq表
        try:
            auth_weibo_model = OAuthWEIBOUser.objects.get(openid=uid)
        except OAuthWEIBOUser.DoesNotExist:
            # 6.1 如果没有查询到,说明: 说明此openid没有和美多用户关联,返回一个关联绑定界面
            openid = generate_openid_signature(uid)
            context = {"openid": openid}
            return render(request, 'sina_callback.html', context)
        else:
            # 6.2 查询到了,说明: 此openid已绑定美多用户,代表登录成功
            # 如果已绑定代表登录成功,真状态保持及重定向来源
            user = auth_weibo_model.user  # 通过外键获取openid关联的user模型对象
            login(request, user)  # 状态保持
            # response = redirect(request.GET.get('state')) ######################
            response = redirect('/')
            response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
            # 合并购物车数据
            merge_cart_cookie_to_redis(request, response)
            return response

    def post(self, request):

       query_dict = request.POST
       mobile = query_dict.get('mobile')
       password = query_dict.get('password')
       sms_code = query_dict.get('sms_code')
       openid = query_dict.get('openid')
       # 2. 校验
       if all([mobile, password, sms_code, openid]) is False:
           return http.HttpResponseForbidden('缺少必传参数')
       if not re.match(r'^1[3-9]\d{9}$', mobile):
           return http.HttpResponseForbidden('请求正确的手机号')
       if not re.match('^[0-9A-Za-z]{8,20}$', password):
           return http.HttpResponseForbidden('请输入8-20位的密码')
       openid = generate_origin_openid(openid)
       if openid is None:
           return http.HttpResponseForbidden('openid无效')

       # 获取redis中短信验证码
       redis_conn = get_redis_connection('verify_codes')
       sms_code_server_bytes = redis_conn.get('sms_code_%s' % mobile)
       # 让短信验证码成为一次性的
       redis_conn.delete('sms_code_%s' % mobile)
       # 判断是否过期
       if sms_code_server_bytes is None:
           return http.HttpResponseForbidden('短信验证码已过期')
       # 转换redis中短信验证码类型
       sms_code_server = sms_code_server_bytes.decode()
       # 判断用户短信验证码是否正确
       if sms_code != sms_code_server:
           return http.HttpResponseForbidden('短信验证码填写错误')
       # 1: 接收表单数据
       # 2: 校验
       #    以mobile字段检查是否是新用户, 不是的话,则把openid和老的user绑定
       #     如果是新用户,则创建一个新的user绑定openid
       # 3:openid 绑定user

       # 1. 接收表单数据: mobile, password, sms_code, openid
       try:
            user = User.objects.get(mobile=mobile)
            if user.check_password(password) is False:
                return http.HttpResponseForbidden('老用户密码错误')
       except User.DoesNotExist:
            # 如果是美多新用户,就创建一个新的user和openid绑定
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)

       # 3. openid 绑定user
       OAuthWEIBOUser.objects.create(
            openid=openid,
            user=user,
        )

        # 状态保持
       login(request, user)
        # 向cookie中存储username
       # response = redirect(request.GET.get('state')) #########################
       response = redirect('/')
       response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        # 响应
       return response