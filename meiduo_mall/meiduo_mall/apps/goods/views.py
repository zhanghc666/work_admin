from django.shortcuts import render
from django import http
from django.utils import timezone
from django.views import View
from django.core.paginator import Paginator, EmptyPage

from contents.utils import get_categories
from goods.models import GoodsCategory, SKU, GoodsVisitCount
from .utils import get_breadcrumb
from meiduo_mall.utils.response_code import RETCODE
from meiduo_mall.utils.views import LoginRequiredView
from orders.models import OrderInfo, OrderGoods


class ListView(View):
    """商品列表界面"""
    def get(self, request, category_id, page_num):
        # 包装面包屑导航数据
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # # 给cat1定义一个url
        # cat1 = cat3.parent.parent
        # cat1.url = cat1.goodschannel_set[0].url
        #
        # # 用来装面包屑数据
        # breadcrumb = {
        #     'cat3': cat3,
        #     'cat2': cat3.parent,
        #     'cat1': cat1
        # }


        # 指定排序规则
        sort = request.GET.get('sort', 'default')

        if sort == 'price':
            sort_fields = '-price'
        elif sort == 'hot':
            sort_fields = '-sales'
        else:
            sort = 'default'
            sort_fields = '-create_time'  # 排序字段

        # 数据分页
        # 获取当前三级类型下的所有sku
        sku_qs = cat3.sku_set.filter(is_launched=True).order_by(sort_fields)

        # 创建分页器对象 参数 (要分页的所有数据, 每页显示多少条数据)
        paginator = Paginator(sku_qs, 5)
        # 获取总页数
        total_page = paginator.num_pages
        # 获取指定页面的数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseForbidden('没有这一页了,别试了')

        context = {
            'categories': get_categories(),  # 频道分类
            'breadcrumb': get_breadcrumb(cat3),  # 面包屑导航
            'sort':sort,  # 排序字段
            'category': cat3,  # 第三级分类
            'page_skus': page_skus,  # 分页后数据
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }
        return render(request, 'list.html', context)


class HotGoodsView(View):
    """商品热销排行"""
    def get(self, request, category_id):
        # 1. 根据三级类型id查询类别
        try:
            cat3 = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        # 2. 截取指定三级类型下的销量最高的前两个sku
        sku_qs = cat3.sku_set.filter(is_launched=True).order_by('-sales')[:2]

        # 3. 模型转字典
        sku_list = []
        for sku in sku_qs:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image.url
            })

        # 4. 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'hot_skus': sku_list})


class DetailView(View):
    """商品详情页"""
    def get(self, request, sku_id):
        try:
            sku = SKU.objects.get(id=sku_id)
        except SKU.DoesNotExist:
            return render(request, '404.html')

        category = sku.category  # 获取当前sku所对应的三级分类

        # 查询当前sku所对应的spu
        spu = sku.spu

        """1.准备当前商品的规格选项列表 [8, 11]"""
        # 获取出当前正显示的sku商品的规格选项id列表
        current_sku_spec_qs = sku.specs.order_by('spec_id')
        current_sku_option_ids = []  # [8, 11]
        for current_sku_spec in current_sku_spec_qs:
            current_sku_option_ids.append(current_sku_spec.option_id)

        """2.构造规格选择仓库
        {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        """
        # 构造规格选择仓库
        temp_sku_qs = spu.skus.all()  # 获取当前spu下的所有sku
        # 选项仓库大字典
        spec_sku_map = {}  # {(8, 11): 3, (8, 12): 4, (9, 11): 5, (9, 12): 6, (10, 11): 7, (10, 12): 8}
        for temp_sku in temp_sku_qs:
            # 查询每一个sku的规格数据
            temp_spec_qs = temp_sku.specs.order_by('spec_id')
            temp_sku_option_ids = []  # 用来包装每个sku的选项值
            for temp_spec in temp_spec_qs:
                temp_sku_option_ids.append(temp_spec.option_id)
            spec_sku_map[tuple(temp_sku_option_ids)] = temp_sku.id

        """3.组合 并找到sku_id 绑定"""
        spu_spec_qs = spu.specs.order_by('id')  # 获取当前spu中的所有规格

        for index, spec in enumerate(spu_spec_qs):  # 遍历当前所有的规格
            spec_option_qs = spec.options.all()  # 获取当前规格中的所有选项
            temp_option_ids = current_sku_option_ids[:]  # 复制一个新的当前显示商品的规格选项列表
            for option in spec_option_qs:  # 遍历当前规格下的所有选项
                temp_option_ids[index] = option.id  # [8, 12]
                option.sku_id = spec_sku_map.get(tuple(temp_option_ids))  # 给每个选项对象绑定下他sku_id属性

            spec.spec_options = spec_option_qs  # 把规格下的所有选项绑定到规格对象的spec_options属性上

        context = {
            'categories': get_categories(),  # 商品分类
            'breadcrumb': get_breadcrumb(category),  # 面包屑导航
            'sku': sku,  # 当前要显示的sku模型对象
            'category': category,  # 当前的显示sku所属的三级类别
            'spu': spu,  # sku所属的spu
            'spec_qs': spu_spec_qs,  # 当前商品的所有规格数据
        }

        return render(request, 'detail.html', context)


class DetailVisitView(View):
    """统计商品类别每日访问量"""
    def post(self, request, category_id):
        # 校验
        try:
            category = GoodsCategory.objects.get(id=category_id)
        except GoodsCategory.DoesNotExist:
            return http.HttpResponseForbidden('category_id不存在')

        date = timezone.now()  # 获取当前的日期和时间
        try:
            # 如果今天这个类别已经记录过,修改它的count += 1
            visit_count = GoodsVisitCount.objects.get(category=category, date=date)
        except GoodsVisitCount.DoesNotExist:
            # 如果今天这个类别还没有访问过,新增一条访问记录,再设置它的count 1
            visit_count = GoodsVisitCount(category=category)

        # 无论是新记录,还是之前已存在的记录都去累加一
        visit_count.count += 1
        visit_count.save()
        # 响应
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK'})


class AllOrders(LoginRequiredView):
    """展示全部订单"""
    def get(self, request, page_num):

        # 查询当前用户所有订单编号
        user = request.user
        order_ids = OrderInfo.objects.filter(user=user).order_by('-create_time')

        order_list = []  # 全部订单数据
        # 遍历得到每一个订单编号
        for order_card in order_ids:
            sku_list = []
            # 查询每个订单下的所有商品
            sku_qs = OrderGoods.objects.filter(order_id=order_card)
            # 遍历得到每一个商品
            for sku_one in sku_qs:
                # 得到每一个商品的信息数据
                try:
                    sku = SKU.objects.get(id=sku_one.sku_id)
                except SKU.DoesNotExist:
                    return http.HttpResponseForbidden('sku_id不存在')
                # 把每个商品的信息存到一个列表中
                sku_list.append({
                    'name': sku.name,
                    'price': sku.price,
                    'default_image': sku.default_image,
                    'count': sku_one.count,
                    'amount': sku_one.count * sku_one.price
                })

            pay_method_name = order_card.PAY_METHOD_CHOICES[int(order_card.pay_method) - 1][1]  # 查询支付方式数字对应的支付名字
            status_name = order_card.ORDER_STATUS_CHOICES[int(order_card.status) - 1][1]  # 查询订单状态数字所对应状态名字

            # 每个订单的大字典数据
            order_list.append({
                'sku_list': sku_list,
                'total_amount': order_card.total_amount,
                'freight': order_card.freight,
                'pay_method_name': pay_method_name,
                'order_id':order_card.order_id,
                'status': order_card.status,
                'status_name':status_name,
                'create_time':order_card.create_time
            })

        # 数据分页
        # 创建分页器对象 参数 (要分页的所有数据, 每页显示多少条数据)
        paginator = Paginator(order_list, 5)
        # 获取总页数
        total_page = paginator.num_pages
        # 获取指定页面的数据
        try:
            page_skus = paginator.page(page_num)
        except EmptyPage:
            return http.HttpResponseForbidden('没有这一页了,别试了')

        context = {
            'page_orders': page_skus,
            'total_page': total_page,  # 总页数
            'page_num': page_num,  # 当前页码
        }

        return render(request, 'user_center_order.html', context)