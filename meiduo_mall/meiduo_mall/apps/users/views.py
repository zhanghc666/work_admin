from random import randint

from django.contrib.auth import login, authenticate, logout
from django.shortcuts import render, redirect
from django.views import View
from django import http
import re
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django_redis import get_redis_connection
import json
# from django.core.mail import send_mail
from django.db import DatabaseError
import logging
logger =  logging.getLogger('django')

from .models import User, Address
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView
from celery_tasks.email.tasks import send_verify_email
from .utils import generate_verify_email_url, get_token_user
from goods.models import SKU
from carts.utils import merge_cart_cookie_to_redis
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from meiduo_mall.libs.yuntongxun.sms import CCP


# apps里面的所有东西导包,无论要导到那里,都依据apps来进行导包
# apps以外的东西无论在那里导包都依据最上层的meiduo_mall进行导包


# Create your views here.
class RegisterView(View):
    """用户注册"""

    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        """注册逻辑"""
        # 1.接受请求表单数据
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code_client = request.POST.get('sms_code')


        # 2.检验
        # 判断参数是否齐全
        if all([username, password, password2, mobile, allow, sms_code_client]) is False:
            return http.HttpResponseForbidden("缺少必传参数")

        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden("请输入5-20个字符的用户")

        if not re.match(r"^[0-9A-Za-z]{8,20}$", password):
            return http.HttpResponseForbidden("请输入8-20位的密码")

        if password != password2:
            return http.HttpResponseForbidden("两次输入的密码不一致")

        if not re.match(r"^1[3-9]\d{9}$", mobile):
            return http.HttpResponseForbidden("您输入的手机号格式不正确")

        # 判断用户短信验证码是否正确
        if allow != "on":
            return http.HttpResponseForbidden("请勾选用户协议")

        # TODO: 校验短信验证码逻辑后期补充
        # 创建redis链接对象
        redis_conn = get_redis_connection('verify_codes')

        sms_code_server_bytes = redis_conn.get('sms_code_%s' % mobile)

        # 设置短信验证码一次性  ################
        redis_conn.delete('sms_code_%s' % mobile)

        # 判断是否过期
        if sms_code_server_bytes is None:
            return http.HttpResponseForbidden('短信验证码已过期')

        # 转换redis中短信验证码类型
        sms_code_server = sms_code_server_bytes.decode()

        # 判断用户短信验证码是否正确
        if sms_code_client != sms_code_server:
            context = {'register_errmsg': '短信验证码错误'}
            return render(request, 'register.html', context)


        # 3.处理业务逻辑
        # user = User.objects.create(username=username, password=password, mobile=mobile)
        # user.set_password(password)
        # user.save()
        user = User.objects.create_user(username=username, password=password, mobile=mobile)

        # 记录用户登录状态: 状态保持
        # 将当前用户的id值存储到session中会生成一个session_id 下次请求时都会把所有cookie带过来
        # 如果cookie中有session_id 并能取到session记录及里面的id 就说明是登录用户
        login(request, user)
        response = redirect('contents:index')
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE)
        # 4.响应
        # return http.HttpResponse("用户注册成功即代表登录成功,登录成功跳转到首页")
        # return redirect('contents:index')
        return response

class UsernameCountView(View):
    """判断用户名是否已重复"""

    def get(self, request, username):
        # 查询username是否已存在
        count = User.objects.filter(username=username).count()
        # 响应
        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})


class MobileCountView(View):
    """判断手机号是否以重复"""

    def get(self, request, mobile):
        count = User.objects.filter(mobile=mobile).count()

        return http.JsonResponse({'count': count, 'code': RETCODE.OK, 'errmsg': 'OK'})


class LoginView(View):
    """用户登陆"""
    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):
        # 1.接收表单数据
        query_dicr = request.POST
        username = query_dicr.get('username')
        password = query_dicr.get('pwd')
        remembered = query_dicr.get('remembered')


        # 2.校验
        if all([username, password]) is False:
            return http.HttpResponseForbidden("缺少必传参数")


        # 3.用户登录验证
        # try:
        #     user = User.objects.get(username=username)
        #     if user.check_password(password) is False:
        #         return http.HttpResponseForbidden('密码错误')
        # except User.DoesNotExist:
        #     return http.HttpResponseForbidden('用户不存在')

        user = authenticate(request, username=username, password=password)
        if user is None:
            return render(request, 'login.html', {"account_errmsg": "账号或密码错误"})


        # 4.状态保持
        login(request, user)

        # 4.1用户登录成功就向cookie中存储username
        response = redirect(request.GET.get('next') or '/')
        # response = redirect('/')
        # settings.SESSION_COOKIE_AGE if remembered else None
        # 如果记住登录就保存cookie中的username有效期14天反之 关闭浏览器就删除
        response.set_cookie('username', user.username, max_age=settings.SESSION_COOKIE_AGE if remembered else None)


        # 4.2如果用户没有记住登录，让状态保持直到关闭浏览器
        if remembered != 'on':
            # request.session.set_expiry(None)  # 如果将session过期时间设置为None就莫恶人读写SESSION_COOKIE_AGE配置时间
            request.session.set_expiry(0)  # 关闭浏览器就删除

            # cookie如果设置过期时间为None 表示关闭浏览器就删除
            # 如果cookie设置过期时间为0, 表示直接删除

        # 5.重定向到首页
        # return http.HttpResponse("登陆成功，去首页")
        # return redirect('contents:index')  # redirect里面可以传递 路由 或 命名空间:路由别名

        # 合并购物车数据
        merge_cart_cookie_to_redis(request,response)
        return response


class LogoutView(View):
    """用户退出"""
    def get(self, request):
        # 1.清除状态保持
        logout(request)


        # 2.清除cookie里的username
        response = redirect('/login/')
        response.delete_cookie('username')

        # 3.重定向到登录页面
        return response


# class InfoView(View):
#     """用户中心"""
#
#     def get(self, request):
#         # if isinstance(request.user, User):
#         user = request.user
#         if user.is_authenticated:  # 判断用户登没登录
#             return render(request, 'user_center_info.html')
#         else:
#             return  redirect('/login/?next=/info/')

class InfoView(LoginRequiredMixin, View):
    """用户中心"""
    def get(self, request):
        return render(request, 'user_center_info.html')


class EmailView(LoginRequiredView):
    """用户邮箱"""
    def put(self, request):
        # 查询当前用户是否已经有了邮箱，如果有了就不要在设置了
        user = request.user
        # 1.获取请求中的非表单数据
        json_str = request.body
        json_dict = json.loads(json_str)
        email = json_dict.get('email')

        # 2.校验
        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('邮箱邮件不正确')

        if user.email == '':
            # 3.设置用户email
            user.email = email
            user.save()

        # verify_url = 'http://www.baidu.com'
        # 拼接邮箱激活url
        verify_url = generate_verify_email_url(user)

        # 3.1 发送验证邮箱的邮件
        # send_mail(subject='邮件主题/标题', message='邮件普通正文/内容', from_email='发件人', recipient_list='收件人列表', html_message='超文本邮件内容')
        # send_mail(subject='美多邮件',
        #           message='',
        #           from_email='美多商城<itcast99@163.com>',
        #           recipient_list=['zhang1076727931@163.com'],
        #           html_message='<a href="http://www.baidu.com">点我试试<a>')
        send_verify_email.delay(email, verify_url)

        # 4.响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})


class EmailVerifyView(View):
    """邮箱激活"""
    def get(self,request):
        # 1.接收查询参数
        token = request.GET.get('token')
        # 2.校验
        user = get_token_user(token)
        if user is None:
            return http.HttpResponseForbidden('token无效')
        # 3.修改email_active字段
        user.email_active = True
        user.save()
        # 4.响应
        return redirect('/info/')


class AddressView(LoginRequiredView):
    """用户收货地址"""

    def get(self, request):
        user = request.user
        # 查询当前用户所有未被逻辑删除的收货地址
        # address_qs = user.addresses.all()  # 查询当前用户所有收货地址
        # address_qs = address_qs.filter(is_deleted=False)
        address_qs = Address.objects.filter(user=user, is_delete=False)
        address_list = []  # 包装每一个地址字典
        for address in address_qs:
            address_list.append({
                'id': address.id,
                'title': address.title,
                'receiver': address.receiver,
                'province_id': address.province_id,
                'province': address.province.name,
                'city_id': address.city_id,
                'city': address.city.name,
                'district_id': address.district_id,
                'district': address.district.name,
                'place': address.detail_address,
                'mobile': address.mobile,
                'tel': address.phone,
                'email': address.email
            })
        context = {
            'addresses': address_list,  # 当前用户所有收货[字典]
            'default_address_id': user.default_address_id
        }

        return render(request, 'user_center_site.html', context)


class AddressCreateView(LoginRequiredView):
    """收货地址新增"""

    def post(self, request):
        # 1. 接收请求体的非表单数据  body
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2. 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式有误')
        if tel:  # 座机号传了再校验,如果没传什么都不做
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')
        user = request.user
        # 3. 新增
        try:
            address = Address(
                user=user,
                title=title,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                detail_address=place,
                mobile=mobile,
                phone=tel,
                email=email
            )
            address.save()
        except DatabaseError as e:
            logger.error(e)
            return http.HttpResponseServerError('存储收货地址失败')

        # 判断当前用户有没有默认收货地址,如果没有,就将当前新增的地址设置为用户的默认地址
        if user.default_address is None:
            user.default_address = address
            user.save()

        # 4. 响应
        # 将新增的address模型对象转换成字典
        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.detail_address,
            'mobile': address.mobile,
            'tel': address.phone,
            'email': address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


class UpdateDestroyAddressView(LoginRequiredView):
    """修改和删除收货地址"""
    def put(self, request, address_id):
        # 1. 接收请求体的非表单数据  body
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        # 2. 校验
        if all([title, receiver, province_id, city_id, district_id, place, mobile]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式有误')
        if tel:  # 座机号传了再校验,如果没传什么都不做
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return http.HttpResponseForbidden('参数tel有误')
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return http.HttpResponseForbidden('参数email有误')

        try:
            address = Address.objects.get(id=address_id)
            address.title = title
            address.receiver = receiver
            address.province_id = province_id
            address.city_id = city_id
            address.district_id = district_id
            address.place = place
            address.mobile = mobile
            address.tel = tel
            address.email = email
            address.save()
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id不存在')

        address_dict = {
            'id': address.id,
            'title': address.title,
            'receiver': address.receiver,
            'province_id': address.province_id,
            'province': address.province.name,
            'city_id': address.city_id,
            'city': address.city.name,
            'district_id': address.district_id,
            'district': address.district.name,
            'place': address.place,
            'mobile': address.mobile,
            'tel': address.tel,
            'email': address.email
        }

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'address': address_dict})


    def delete(self, request, address_id):
        """删除指定收货地址"""
        # 查询要被逻辑删除的收货地址
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id不存在')

        address.is_deleted = True
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class DefaultAddressView(LoginRequiredView):
    """修改默认地址"""
    def put(self, request, address_id):
        # 查询address
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id不存在')

        user = request.user
        # 修改当前user的default_address的字段
        user.default_address = address
        user.save()

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class UpdateAddressTitleView(LoginRequiredView):
    """修改用户地址标题"""
    def put(self, request, address_id):
        # 接收请求数据
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        # 查询要修改标题的收货地址
        try:
            address = Address.objects.get(id=address_id)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id不存在')

        # 修改它的title字段并save
        address.title = title
        address.save()

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class ChangePasswordView(LoginRequiredView):
    """修改用户密码"""
    def get(self, request):
        return render(request, 'user_center_pass.html')

    def post(self, request):
        # 1.接收表单数据
        json_dict = request.POST
        old_pwd = json_dict.get('old_pwd')
        new_pwd = json_dict.get('new_pwd')
        new_cpwd = json_dict.get('new_cpwd')

        # 2.校验
        if all([old_pwd, new_pwd, new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        user = request.user
        if user.check_password(old_pwd) is False:
            return render(request, 'user_center_pass.html', {'origin_pwd_errmsg': '原始密码不正确'})

        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        # 3.修改密码
        user.set_password(new_pwd)
        user.save()

        # 4.重定向到登录页面
        logout(request)
        response = redirect('/login/')
        response.delete_cookie('username')

        return response


class UserBrowseHistory(View):
    """用户商品浏览记录"""
    def post(self, request):
        # 判断当前请求,是不是登录用户,如果不是直接响应
        user = request.user
        if not user.is_authenticated:
            return http.JsonResponse({'code': RETCODE.SESSIONERR, 'errmsg': '用户未登录,不给服务'})

        # 1.获取请求体数据
        json_dict = json.loads(request.body.decode())  # 把数据转成json字典
        sku_id = json_dict.get('sku_id')
        # 2.校验
        try:
            sku = SKU.objects.get(id= sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')
        # 3.业务逻辑代码
        # 3.1创建redis链接对象
        redis_conn = get_redis_connection('history')
        pl = redis_conn.pipeline()
        key = 'history_%s' % user.id
        # 3.2列表去重
        pl.lrem(key, 0, sku_id)
        # 3.3向列表开头添加数据
        pl.lpush(key, sku_id)
        # 3.5截取列表前5个数据
        pl.ltrim(key, 0, 4)
        # 3.6执行管道
        pl.execute()
        # 4.响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

    def get(self, request):
        """获取商品浏览记录"""
        # 创建redis链接对象
        redis_conn = get_redis_connection('history')

        user = request.user
        if not user.is_authenticated:
            return http.HttpResponseForbidden('请登陆')

        # 获取出当前用户的所有商品浏览记录数据
        key = 'history_%s' % user.id

        sku_ids = redis_conn.lrange(key, 0, -1)

        # 通过sku_id将对应的sku模型查询
        # sku_qs = SKU.objects.filter(id__in=sku_ids)
        sku_list = []  # 用来包装所有sku字典
        for sku_id in sku_ids:
            sku = SKU.objects.get(id=sku_id)
            # 模型转字典
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'skus': sku_list})


# class FindPassword(View):
#     """获取修改密码界面"""
#     def get(self, request):
#         return render(request, 'find_password.html')
#
#
# class InputID(View):
#     """输入账号"""
#     def get(self, request, username):
#         # 接收参数
#         username = username
#         text = request.GET.get('text')
#         image_code_id = request.GET.get('image_code_id')
#
#         # 校验
#         if all([username, text, image_code_id]) is False:
#             return http.HttpResponseForbidden("缺少必传参数")
#
#         return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
#
#     def post(self, request):
#         # 接收参数
#         username = request.POST.get('username')
#         image_code = request.POST.get('image_code')
#         text = request.GET.get('text')
#
#         # 校验
#         if all([username, image_code]) is False:
#             return http.HttpResponseForbidden("缺少必传参数")
#
#         if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
#             return http.HttpResponseForbidden("请输入5-20个字符的用户")
#
#         if not image_code == text:
#             return  http.HttpResponseForbidden('验证码不对')
#
#         return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class Find_Password(View):
    """展示忘记密码页面"""
    def get(self,request):
        return render(request,'find_password.html')


class Find_Password_Username(View):
    def get(self,request,username):
        """接收用户名"""
        try:
            # 取出数据库中手机号
            user_lost=User.objects.get(username=username)
            mobile = user_lost.mobile
        except:
            return http.JsonResponse({'error':'...'},status=400)

        image_code_client = request.GET.get('text')
        uuid = request.GET.get('image_code_id')

        if all([image_code_client, uuid]) is False:
            return http.HttpResponseForbidden('缺少参数')
        # 2.校验图片验证码
        # 取出redis中数据
        redis_conn = get_redis_connection('verify_codes')
        image_code_server_bytes = redis_conn.get(uuid)

        # 3验证码是否输入
        if image_code_server_bytes is None:
            return http.JsonResponse({'error':'yzm  null'},status=400)

        image_code_server = image_code_server_bytes.decode()

        if image_code_server.lower() != image_code_client.lower():
            return http.JsonResponse({'error':'yzm XXX'},status=400)
        # 加密后的数据
        serializer = Serializer(settings.SECRET_KEY, expires_in=60*5)
        access_token=serializer.dumps({'mobile':mobile})
        access_token=access_token.decode()

        return http.JsonResponse({'message':'ok','access_token':access_token,'mobile':mobile})

class Create_SMS(View):
    def get(self, request):
        # 手机号，access_token
        access_token=request.GET.get('access_token')
        serializer = Serializer(settings.SECRET_KEY, expires_in=60*5)
        access_token = serializer.loads(access_token)

        sms_codes = "%06d" % randint(0, 999999)
        # 生成验证码（容联云通信）
        mobile=access_token['mobile']
        CCP().send_template_sms(mobile, [sms_codes, 5], 1)
        print(sms_codes)
        # 存进redis
        redis_conn = get_redis_connection('verify_codes')
        redis_conn.setex('sms_code%s' % mobile, 300, sms_codes)
        return http.JsonResponse({'message': 'ok'})

class Find_Password_SMS(View):
    """短信验证码验证"""
    def get(self,request,username):

        sms_code_client = request.GET.get('sms_code')

        # 验证码校验
        # 取出redis数据库中验证码(sms_187....)
        user=User.objects.get(username=username)
        mobile=user.mobile
        redis_conn = get_redis_connection('verify_codes')

        sms_code_server_bytes = redis_conn.get('sms_code%s' % mobile)
        # 设置短信验证码只能使用一次
        redis_conn.delete('sms_code%s' % mobile)
        if sms_code_server_bytes is None:
            return http.HttpResponseForbidden('验证码已过期')

        if sms_code_client != sms_code_server_bytes.decode():
            return http.JsonResponse({'error': 'SMS XXX'}, status=400)
        user_lost = User.objects.get(username=username)
        user_id=user_lost.id
        print("SMS AAA")

        # 验证码加密
        serializer = Serializer(settings.SECRET_KEY, expires_in=60 * 5)
        access_token = serializer.dumps({'sms_code':sms_code_client})
        access_token = access_token.decode()

        return http.JsonResponse({'message':'ok','user_id':user_id,'access_token':access_token})

class Find_Password_Reset(View):
    """重置密码"""
    def post(self,request,user_id):
        request.META["CSRF_COOKIE_USED"] = True
        new_password = json.loads(request.body.decode())
        new_pwd = new_password.get('password')
        new_cpwd = new_password.get('password2')

        access_token = new_password.get('access_token')
        serializer = Serializer(settings.SECRET_KEY, expires_in=60 * 5)
        access_token = serializer.loads(access_token)
        sms_code=access_token['sms_code']

        # 校验
        if all([new_pwd,new_cpwd]) is False:
            return http.HttpResponseForbidden('缺少参数')
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_pwd):
            return http.HttpResponseForbidden('密码最少8位，最长20位')
        if new_pwd != new_cpwd:
            return http.HttpResponseForbidden('两次输入的密码不一致')


        # 3修改用户密码
        user=User.objects.get(id=user_id)
        user.set_password(new_pwd)
        user.save()

        print(new_pwd)


        return http.JsonResponse({'message':'ok'})
