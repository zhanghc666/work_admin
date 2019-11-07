from decimal import Decimal
from django.shortcuts import render
from django.utils import timezone
from django_redis import get_redis_connection
import json
from django import http
from django.db import transaction
from django.views import View


from meiduo_mall.utils.views import LoginRequiredView
from users.models import Address, User
from goods.models import SKU
from .models import OrderGoods, OrderInfo
from meiduo_mall.utils.response_code import RETCODE
import logging

logger = logging.getLogger('django')


class OrderSettlementView(LoginRequiredView):
    """去结算界面"""
    def get(self,request):
        user = request.user
        # 查询当前登录用户的所有未被逻辑的收货地址
        addresses = Address.objects.filter(user=user, is_delete=False)

        # 创建redis连接
        redis_conn = get_redis_connection('carts')
        # 获取当前登录用户redis中所有购物车数据
        redis_carts = redis_conn.hgetall('carts_%s' % user.id)
        selected_id = redis_conn.smembers('selected_%s' % user.id)
        # 对redis购物车数据进行过滤,只要那些勾选的商品sku_id和count
        cart_dict = {}  # {sku_id: count, sku_id: count}
        for sku_id_bytes in selected_id:
            cart_dict[int(sku_id_bytes)] = int(redis_carts[sku_id_bytes])

        # 将勾选的所有sku_id对应的sku全部查询
        sku_qs = SKU.objects.filter(id__in=cart_dict.keys())
        # 定义一个用来记录商品总数量
        total_count = 0
        total_amount = Decimal('0.00')
        # 遍历sku查询集,给每个sku模型多定义 count和amount属性
        for sku in sku_qs:
            sku.count = cart_dict[sku.id]
            sku.amount = sku.price * sku.count  # 小计

            total_count += sku.count  # 数量累加
            total_amount += sku.amount  # 小计累加

        # 运费
        freight = Decimal('10.00')
        # 计算实付金额
        payment_amount = total_amount + freight

        context = {
            'addresses': addresses,  # 收货地址
            'skus': sku_qs,  # 购物车中勾选商品数据
            'total_count': total_count,  # 要购买商品总数量
            'total_amount': total_amount,  # 商品总金额
            'freight': freight,  # 运费
            'payment_amount': payment_amount,  # 实付金额
        }
        return render(request, 'place_order.html', context)



class OrderCommitView(LoginRequiredView):
    """提交订单"""

    def post(self, request):
        # 1.接收
        json_dict = json.loads(request.body.decode())
        address_id = json_dict.get('address_id')
        pay_method = json_dict.get('pay_method')

        # 2. 校验
        if all([address_id, pay_method]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        user = request.user
        try:
            address = Address.objects.get(id=address_id, user=user, is_delete=False)
        except Address.DoesNotExist:
            return http.HttpResponseForbidden('address_id有误')

        if pay_method not in [OrderInfo.PAY_METHODS_ENUM['CASH'], OrderInfo.PAY_METHODS_ENUM['ALIPAY']]:
            return http.HttpResponseForbidden('支付方式有误')

        # 订单编号: 20191024111633000000001
        order_id = timezone.now().strftime('%Y%m%d%H%M%S') + '%09d' % user.id
        # 判断订单初始状态
        # 如果选择支付宝支付，订单状态为待付款；否则订单状态为待发货
        status = (OrderInfo.ORDER_STATUS_ENUM['UNPAID'] if
                  (pay_method == OrderInfo.PAY_METHODS_ENUM['ALIPAY']) else
                  OrderInfo.ORDER_STATUS_ENUM['UNSEND'])

        # 手动开启事务
        with transaction.atomic():

            # 创建事务保存点
            save_point = transaction.savepoint()
            try:
                # 新增订单记录  OrderInfo  (一)
                order = OrderInfo.objects.create(
                    order_id=order_id,
                    user=user,
                    address=address,
                    total_count=0,
                    total_amount=Decimal('0.00'),
                    freight=Decimal('10.00'),
                    pay_method=pay_method,
                    status=status
                )

                # 创建redis连接
                redis_conn = get_redis_connection('carts')
                # 获取hash和set数据
                redis_carts = redis_conn.hgetall('carts_%s' % user.id)
                selected_ids = redis_conn.smembers('selected_%s' % user.id)
                # 对购物车数据进行过滤,只留下要勾选商品的sku_id和count
                cart_dict = {}  # {sku_id: count}
                for sku_id in selected_ids:
                    cart_dict[int(sku_id)] = int(redis_carts[sku_id])

                # 遍历cart_dict 进行一个一个商品下单
                for sku_id in cart_dict:
                    while True:
                        # 通过sku_id查询sku模型
                        sku = SKU.objects.get(id=sku_id)
                        # 获取当前商品要购买的数量
                        buy_count = cart_dict[sku_id]
                        origin_stock = sku.stock  # 商品原库足
                        origin_sales = sku.sales  # 商品原销量

                        # 判断库存是否充足
                        if buy_count > origin_stock:
                            # 库足不足回滚
                            transaction.savepoint_rollback(save_point)
                            return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '库存不足'})

                        # 修改SKU的库存和销量
                        new_stock = origin_stock - buy_count  # 新库存
                        new_sales = origin_sales + buy_count  # 新销量
                        # sku.stock = new_stock
                        # sku.sales = new_sales
                        # sku.save()
                        # 使用乐观锁解决商品超卖问题
                        result = SKU.objects.filter(id=sku_id, stock=origin_stock).update(stock=new_stock, sales=new_sales)
                        if result == 0:  # 修改失败
                            continue
                        # 修改SPU的销量
                        spu = sku.spu
                        spu.sales += buy_count
                        spu.save()

                        # 新增N个订单中商品记录  OrderGoods (多)
                        OrderGoods.objects.create(
                            order=order,
                            sku=sku,
                            count=buy_count,
                            price=sku.price
                        )

                        # 修改订单记录中的购买商品总数量#修改商品总价
                        order.total_count += buy_count
                        order.total_amount += (sku.price * buy_count)
                        break  # 当前商品下单成功跳出死循环

                # 最终累加运费
                order.total_amount += order.freight
                order.save()
            except Exception as e:
                logger.error(e)
                # 暴力回滚
                transaction.savepoint_rollback(save_point)
                return http.JsonResponse({'code': RETCODE.STOCKERR, 'errmsg': '下单失败'})
            else:
                # 提交事务
                transaction.savepoint_commit(save_point)

        # 将购物车中已结算商品删除
        pl = redis_conn.pipeline()
        pl.delete('selected_%s' % user.id)
        pl.hdel('carts_%s' % user.id, *selected_ids)
        pl.execute()
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'order_id': order_id})


class OrderSuccessView(LoginRequiredView):
    """订单提交成功界面"""

    def get(self, request):
        # 1.获取数据
        query_dict = request.GET
        payment_amount = query_dict.get('payment_amount')
        order_id = query_dict.get('order_id')
        pay_method = query_dict.get('pay_method')

        user = request.user
        try:
            OrderInfo.objects.get(order_id=order_id, pay_method=pay_method, total_amount=payment_amount, user=user)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('订单有误')

        context = {
            'payment_amount': payment_amount,
            'order_id': order_id,
            'pay_method': pay_method
        }
        return render(request, 'order_success.html', context)


class GoodsComment(LoginRequiredView):
    """商品评价"""

    def get(self, request):
        # 接收数据
        order_id = request.GET.get('order_id')
        # 校验
        try:
            # 查询当前订单是否存在
            order = OrderInfo.objects.get(order_id=order_id)
        except OrderInfo.DoesNotExist:
            return http.HttpResponseForbidden('order_id不存在')
        # 查询当前订单下所有商品
        sku_qs = OrderGoods.objects.filter(order_id=order)
        uncomment_goods_list = []

        # 遍历一个订单所有商品,得到每一个商品
        for sku_one in sku_qs:
            # 在商品表中查询每一个商品
            sku = SKU.objects.get(id=sku_one.sku_id)
            if sku_one.is_commented == 1:  # 如果当前商品已有评论信息就跳过
                continue
            uncomment_goods_list.append({
                'order_id': order_id,
                'sku_id':sku.id,
                'default_image_url': sku.default_image.url,
                'name': sku.name,
                'price': str(sku.price)
            })

        context = {'uncomment_goods_list': uncomment_goods_list}

        return render(request, 'goods_judge.html', context=context)

    def post(self, request):
        # 接收数据
        json_dict = json.loads(request.body.decode())
        order_id = json_dict.get('order_id')
        sku_id = json_dict.get('sku_id')
        comment = json_dict.get('comment')
        score = json_dict.get('score')
        is_anonymous = json_dict.get('is_anonymous')

        # 校验
        if all([order_id, sku_id, comment, score]) is False:
            return http.HttpResponseForbidden('缺少必传参数')

        # 保存信息(每一个商品的评价)
        try:
            good_order = OrderGoods.objects.filter(order_id = order_id, sku_id = sku_id).update(
                is_commented = 1,
                comment=comment,
                score=score,
                is_anonymous=is_anonymous
            )
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '提价评价失败'})

        # 判断当前订单下所有商品是否都已经评价，如果评价了，就把状态改为已评价
        goods_qs = OrderGoods.objects.filter(order_id=order_id)

        for goods in goods_qs:
            if goods.is_commented == 0:  # 如果商品没有评论就跳出去,有评价就继续循环
                return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})

        OrderInfo.objects.filter(order_id=order_id).update(status= OrderInfo.ORDER_STATUS_ENUM['FINISHED'])

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class CommentView(View):
    """商品详情页评论"""
    def get(self, request, sku_id):
        # 查询订单商品信息
        orders = OrderGoods.objects.filter(sku_id=sku_id)  # 得到所有编号为sku_id的商品

        comment_list = []  # 所有已评论的 用户和内容 的列表
        for order in orders:  # 得到该商品每条订单记录

            if order.comment:  # 如果该商品订单记录中有评论信息
                orderid = order.order_id
                info = OrderInfo.objects.get(order_id=orderid)  #查出订单信息表中orderid订单的记录
                user = User.objects.get(id=info.user_id)  # 通过订单记录查出该订单用户名
                # 包装评论字典
                comment_list.append({
                    'name': user.username,
                    'comment': order.comment
                })
            else:  # 如果没有评论记录跳过本次
                continue
        return http.JsonResponse({"comment_list": comment_list})
