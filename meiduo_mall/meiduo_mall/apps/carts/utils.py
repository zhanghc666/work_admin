import pickle, base64
from django_redis import get_redis_connection

def merge_cart_cookie_to_redis(request, response):
    """
    登录时合并购物车数据,将cookie购物车数据向redis中添加
    """
    # 1.获取cookie购物车数据
    cart_str = request.COOKIES.get('carts')

    # 2. 如果没有cookie数据,提前return
    if cart_str is None:
        return

    # 3. 将cart_str ---> cart_dict
    cart_dict = pickle.loads(base64.b64decode(cart_str.encode()))

    # 创建redis链接对象
    redis_conn = get_redis_connection('carts')
    user = request.user
    # 遍历cookie大字典,将数据分别向hash和set中添加
    for sku_id in cart_dict:
        # 把数据添加到hash中
        redis_conn.hset('carts_%s' % user.id, sku_id, cart_dict[sku_id]['count'])
        # 把数据添加到set中
        if cart_dict[sku_id]['selected']:
            redis_conn.sadd('selected_%s' % user.id, sku_id)
        else:
            redis_conn.srem('selected_%s' % user.id, sku_id)

    # 合并完成并删除cookie中的购物车数据
    response.delete_cookie('carts')