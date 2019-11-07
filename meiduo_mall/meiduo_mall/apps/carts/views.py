from django.shortcuts import render
from django.views import View
import json
from django import http
import pickle, base64
from django_redis import get_redis_connection


from goods.models import SKU
from meiduo_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class CartsView(View):
    """购物车操作"""
    def post(self, request):
        """购物车新增"""

        # 1.接收请求体数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected', True)

        # 2.校验
        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        try:
            sku = SKU.objects.get(id = sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')
        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('count类型有误')

        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('selected类型有误')

        # 3.判断用户是否登录
        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车数据成功'})
        if user.is_authenticated:
            """
            hash: {sku_id_1: count, sku_id_2: count}
            set: {sku_id_1}
            """
            # 如果是登录用户,就存储购物车数据到redis
            # 创建redis连接
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 将sku_id和count向hash中添加
            # hincrby(key:区分redis的那个hash, 向hash中添加的属性/key, value) 会累加
            pl.hincrby('carts_%s' % user.id, sku_id, count)
            # 如果当前商品是勾选的就将它的sku_id添加到set集合中
            if selected:
                pl.sadd('selected_%s' % user.id, sku_id)
            pl.execute()
            # 响应
            # return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车数据成功'})
        else:
            # 如果是未登录用户，就存储购物车数据到cookie
            # 先获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                # 如果获取到cookie购物车数据
                # 将它从字符串转换回字典
                # 将str ---> b'xxx'
                cart_str_bytes = cart_str.encode()
                # 将b'xxdsd' --> b'0xfds'
                cart_str_bytes_un = base64.b64decode(cart_str_bytes)
                # 将b'0xfds' --> dict
                cart_dict = pickle.loads(cart_str_bytes_un)

                # 判断当前要添加到商品在cookie大字典中是否已存在,如果存在,累加count
                if sku_id in cart_dict:
                    origin_count = cart_dict[sku_id]['count']
                    count += origin_count
            else:
                # 定义一个空字典,准备包装购物车数据
                cart_dict = {}

            # 将新的商品数据添加到cookie大字典中
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }

            # 将cookie购物车大字典转换成字符串
            # dict ---> b'0x2'
            cart_str_bytes_un = pickle.dumps(cart_dict)
            # b'0x2' ---> b'fdsfds'
            cart_str_bytes = base64.b64encode(cart_str_bytes_un)
            # b'fdsfds' --> str
            cart_str = cart_str_bytes.decode()
            # 设置cookie
            # response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加购物车成功'})
            response.set_cookie('carts', cart_str)
        # 响应
        return response

    def get(self, request):
        """购物车展示"""
        """
        {
            sku_id: {'count': 1, 'selected': True}

        }
        """
        user = request.user
        if user.is_authenticated:
            # 登录用户获取redis购物车数据

            # 创建redis链接对象
            redis_conn = get_redis_connection('carts')
            # 获取hash数据 {sku_id: count}  获取当前用户购物车所有商品id及数量
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取set中数据 {sku_id, sku_id}  获取购物车勾选商品
            selected_ids = redis_conn.smembers('selected_%s' % user.id)
            # 将redis购物车数据包装成和cookie购物车数据格式一致
            cart_dict = {}  # 包装redis购物车的所有数据
            for sku_id_bytes in redis_carts:  # 默认遍历字典的建
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),  # 购物车中当前sku_id_bytes商品的数量
                    'selected': sku_id_bytes in selected_ids  # 判断当前sku_id_bytes商品是否在勾选商品中
                }
        else:
            # 未登录用户获取cookie购物车数据

            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')
            # 判断是否获取到cookie购物车数据
            if cart_str:
                # 如果有cookie购物车数据,将str转换成字典
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie购物车数据,直接响应一个空白购物车界面
                return render(request, 'cart.html')

        # 通过sku_id查询出sku模型
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())  # 得到购物车中商品的详细信息（sku）的查询集

        sku_list = [] # 用来包装sku字典
        # 模型转字典
        for sku in sku_qs:  # sku：得到每一件商品sku对象
            count = cart_dict[sku.id]['count']
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url,
                'count': count,
                'selected': str(cart_dict[sku.id]['selected']),
                'amount': str(sku.price * count)
            })
        # 把数据通过渲染模板的方式传递给前端
        return render(request, 'cart.html', {'cart_skus': sku_list})

    def put(self, request):
        """购物车修改"""

        # 1.接收请求数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')
        count = json_dict.get('count')
        selected = json_dict.get('selected')

        # 2.校验
        if all([sku_id, count]) is False:
            return http.HttpResponseForbidden('缺少必传参数')
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')
        try:
            count = int(count)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseForbidden('count类型有误')

        if isinstance(selected, bool) is False:
            return http.HttpResponseForbidden('selected类型有误')

        # 响应
        sku_dict = {
            'id': sku.id,
            'name': sku.name,
            'price': sku.price,
            'default_image_url': sku.default_image.url,
            'count': count,
            'selected': selected,
            'amount': sku.price * count
        }

        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_sku': sku_dict})
        user = request.user
        if user.is_authenticated:
            # 如果用户登录操作redis数据库

            # 1.创建redis链接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 修改hash数据  {sku_id: count}
            pl.hset('carts_%s' % user.id, sku_id, count)  # 修改当前商品数量
            # 修改set数据 {sku_id}
            if selected:
                # 勾选就将sku_id添加到set中
                pl.sadd('selected_%s' % user.id, sku_id)
            else:
                # 不勾选就将sku_id从set中移除
                pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
        else:
            # 如果用户未登录操作cookie

            # 获取cookie数据
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 如果有cookie就将它从str--->dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有cookie购物车数据
                # 提前响应
                return http.HttpResponseForbidden('非法用户')

            # 修改购物车字典数据
            cart_dict[sku_id] = {
                'count': count,
                'selected': selected
            }
            # 将cookie dict --> str
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            # 设置cookie
            response.set_cookie('carts', cart_str)

        return response

    def delete(self, request):
        """购物车删除"""
        # 1.接收数据
        json_dict = json.loads(request.body.decode())
        sku_id = json_dict.get('sku_id')

        # 2.校验
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return http.HttpResponseForbidden('sku_id不存在')

        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        if user.is_authenticated:
            # 如果登录用户，就操作redis

            # 创建redis链接对象
            redis_conn = get_redis_connection('carts')
            pl = redis_conn.pipeline()
            # 删除hash中的数据
            pl.hdel('carts_%s' % user.id, sku_id)
            # 删除set中的数据
            pl.srem('selected_%s' % user.id, sku_id)
            pl.execute()
        else:
            # 如果未登录用户，就操作cookie

            # 获取cookie数据
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 如果有cookie数据，就把str转成dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 没有获取cookie, 提前响应
                return http.HttpResponseForbidden('非法用户')
            # 删除cookie字典中指定的键值对
            if sku_id in cart_dict:
                del cart_dict[sku_id]

            if not cart_dict:  # 如果将 {} [], '' 放在if后面作为条件都是不成功
                response.delete_cookie('carts')  # 如果用户的cookie购物车数据已经没有商品直接将cookie删除
                return response
            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()

            response.set_cookie('carts', cart_str)

        return response


class CartsSimpleView(View):

    def get(self, request):
        """简单版购物车展示"""
        """
        {
            sku_id: {'count': 1, 'selected': True}

        }
        """
        user = request.user
        if user.is_authenticated:
            # 登录用户操作redis购物车数据
            redis_conn = get_redis_connection('carts')
            # 获取hash数据 {sku_id: count}  获取当前用户购物车所有商品id及数量
            redis_carts = redis_conn.hgetall('carts_%s' % user.id)
            # 获取set中数据 {sku_id, sku_id}  获取购物车勾选商品
            selected_ids = redis_conn.smembers('selected_%s' % user.id)

            cart_dict = {}
            for sku_id_bytes in redis_carts:
                cart_dict[int(sku_id_bytes)] = {
                    'count': int(redis_carts[sku_id_bytes]),
                    'selected': sku_id_bytes in selected_ids
                }
        else:
            # 未登录用户操作cookie购物车数据

            # 获取cookie数据
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                return render(request, 'cart.html')

        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())

        sku_list = []
        # 模型转字典
        for sku in sku_qs:
            count = cart_dict[sku.id]['count']
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': str(sku.price),
                'default_image_url': sku.default_image.url,
                'count': count,
                'selected': str(cart_dict[sku.id]['selected']),
                'amount': str(sku.price * count)
            })

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'cart_skus': sku_list})


class CartsSelectedAllView(View):
    """购物车全选"""
    def put(self,request):
        # 1.接收数据
        json_dict = json.loads(request.body.decode())
        selected = json_dict.get('selected')

        # 2.检验
        if isinstance(selected, bool) is False:  # 如果selected不是布尔类型
            return http.HttpResponseForbidden('类型有误')

        user = request.user
        response = http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})
        if user.is_authenticated:
            # 如果是登录用户，就操作redis
            # 创建redis链接对象
            redis_conn = get_redis_connection('carts')
            # 判断当前是要全选,还是取消全选
            if selected:  # 全选就将hash中数据取出来,并拿到所有sku_id,添加到set中
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)  # 获取到当前用户购物车所有商品
                redis_conn.sadd('selected_%s' % user.id, *redis_carts.keys())  # 把购物车所有商品id添加到set
            else:
                redis_conn.delete('selected_%s' % user.id)
        else:
            # 如果是未登录用户，就操作cookie
            # 获取cookie购物车数据
            cart_str = request.COOKIES.get('carts')

            if cart_str:
                # 如果有,将它从str 转 成 dict
                cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))
            else:
                # 如果没有,提前响应
                return http.HttpResponseForbidden('没有数据')

            # 遍历cookie大字典将selected改成True或False
            for sku_id in cart_dict:
                cart_dict[sku_id] = {
                    'count': cart_dict[sku_id]['count'],
                    'selected': selected
                }

            cart_str = base64.b64encode(pickle.dumps(cart_dict)).decode()
            response.set_cookie('carts', cart_str)

        return response