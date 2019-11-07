
from rest_framework.views import APIView
from rest_framework.response import Response
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.conf import settings
import pytz
from rest_framework_extensions.cache.decorators import cache_response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action


from users.models import User
from orders.models import OrderInfo
from goods.models import GoodsVisitCount

# from rest_framework_extensions.cache.mixins import ListCacheResponseMixin,RetrieveCacheResponseMixin,CacheResponseMixin
# 视图缓存：将视图返回的数据缓存到redis中，便于下一次访问该视图，直接从redis中提取数据


class HomeViewSet(ViewSet):

    @action(methods=['get'], detail=False)  # detail=False直接拼接前缀
    @cache_response(timeout=60)
    def total_count(self, request):
        """1、用户总数统计"""
        # 1.统计用户总数
        count = User.objects.all().count()

        # datetime.now() --> 当前时间！！时区
        # 1、获得时间戳 1572856748  --> 零时区作为基准
        # 2、1970年 + 获得时间戳 = 时间点（零时区）
        # 3、时间点（零时区） --> 根据操作系统的时区 --> 转化成本地时间
        # cur_date = datetime.now()
        # timezone.now() --> 当前0时区的时间点
        tz_shanghai = pytz.timezone(settings.TIME_ZONE)
        # astimezone(tz=目标时区）：将一个时间点从一个时区转换到目标时区
        cur_date = timezone.now().astimezone(tz=tz_shanghai)
        # 2019-11-04  16:00:57.123456 Asia/Shanghai
        print(cur_date)

        # 2、构建响应数据
        return Response({
            "count": count,
            "date": cur_date.date()  # 当前时区当日年月日信息
        })

    @action(methods=['get'], detail=False)
    @cache_response(timeout=60)
    def day_increment(self, reqeust):
        """2、统计"今天"(当前服务器所处的时区)，新建的用户"""

        # 1、当日的"零时"
        # 当前服务器所在时区的当前时刻！！
        cur_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))
        # 当前服务器定义的时区的当日零时刻
        # 2019-11-4 0:0:0.000000 Asia/Shanghai
        cur_0_time = cur_time.replace(hour=0, minute=0, second=0, microsecond=0)

        user_count = User.objects.filter(date_joined__gte=cur_0_time).count()

        return Response({
            "count": user_count,
            "date": cur_0_time
        })

    @action(methods=['get'], detail=False)
    @cache_response(timeout=60)
    def day_active(self, request):
        """3.日活跃用户统计"""
        cur_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))
        cur_0_time = cur_time.replace(hour=0, minute=0, second=0, microsecond=0)

        user_count = User.objects.filter(last_login__gte=cur_0_time).count()

        return Response({
            "count": user_count,
            "date": cur_0_time
        })

    @action(methods=['get'], detail=False)
    @cache_response(timeout=60)
    def day_orders(self, request):
        """4.日下单用户统计"""
        cur_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))
        cur_0_time = cur_time.replace(hour=0, minute=0, second=0, microsecond=0)

        # 获得当日所有订单记录
        order_qs = OrderInfo.objects.filter(create_time__gte=cur_0_time)

        user_list = []
        for order in order_qs:
            user_list.append(order.user)

        user_count = len(set(user_list))

        return Response({
            "count": user_count,
            "date": cur_0_time.date()
        })

    @action(methods=['get'], detail=False)
    @cache_response(timeout=60)
    def month_increment(self, request):
        """5.月下单用户统计"""
        # 获取当前日期
        cur_time = timezone.now().astimezone(tz=pytz.timezone(settings.TIME_ZONE))
        now_day = cur_time.replace(hour=0, minute=0, second=0, microsecond=0)
        # now_day = date.today()
        # 获取一个月前日期
        start_day = now_day - timedelta(29)
        # 保存每天的用户量
        day_list = []

        for i in range(30):
            index_day = start_day + timedelta(days=i)  # 每一天的0.00点
            next_day = index_day + timedelta(days=1)  # 每一天的24.00点
            count = User.objects.filter(date_joined__gte=index_day, date_joined__lt=next_day).count()
            day_list.append({
                "count": count,
                "date": index_day.date()
            })

        return Response(day_list)

    @action(methods=['get'], detail=False)
    @cache_response(timeout=60)
    def goods_day_views(self, request):
        """6.日分类商品访问量"""
        # 当前日期
        now_day = date.today()

        category_list = []
        visit_qs = GoodsVisitCount.objects.filter(date=now_day)

        for visit in visit_qs:
            count = visit.count
            category = visit.category.name
            category_list.append({
                "count": count,
                "category": category
            })
        return Response(category_list)



