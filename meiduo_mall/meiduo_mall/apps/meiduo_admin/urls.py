from django.conf.urls import url
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import SimpleRouter

from meiduo_admin.views.login_view import *
from meiduo_admin.views.home_views import *
from meiduo_admin.views.user_view import *
from meiduo_admin.views.sku_view import *
from meiduo_admin.views.spu_view import *
from meiduo_admin.views.speci_view import *
from meiduo_admin.views.option_view import *
from meiduo_admin.views.image_view import *

urlpatterns = [
    # url(r'^authorizations/$', LoginAPIview.as_view()),
    url(r'^authorizations/$', obtain_jwt_token),  # jwt认证

    # url(r'^statistical/total_count/$', UserTotal.as_view()),  # 用户总数统计
    # url(r'^statistical/day_increment/$', UserDayIncrAPIView.as_view()),  # 日增用户统计
    # url(r'^statistical/day_active/$', UserDayActiveAPIView.as_view()),  # 日活跃用户统计
    # url(r'^statistical/day_orders/$', UserOrderCountAPIView.as_view()),  # 日下单用户量统计
    # url(r'^statistical/month_increment/$', UserMonthCountAPIView.as_view()),  # 月下单用户统计
    # url(r'^statistical/goods_day_views/$', GoodsDayView.as_view()),  # 日分类商品访问量

    url(r'^users/$', UserAPIView.as_view()),  # 用户管理模块

    # 商品管理模块
    url(r'^skus/$', SKUViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^skus/(?P<pk>\d+)/$', SKUViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    url(r'^skus/categories/$', GoodsCategoryView.as_view()),  # 三级分类信息
    url(r'^goods/simple/$', SPUSimpleView.as_view()),  # spu表名称数据
    url(r'^goods/(?P<pk>\d+)/specs/$', SpecOptView.as_view()),  # spu表名称数据

    # SPU表管理
    url(r'^goods/$', SPUViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^goods//$', SPUViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    url(r'^goods/brands/simple/$', BrandSimpleView.as_view()),  # 品牌数据
    url(r'^goods/channel/categories/$', GoodsCategoriteView.as_view()),  # 一级分类信息
    url(r'^goods/channel/categories/(?P<pk>\d+)/$', GoodsCategoriteView.as_view()),  # 一级分类信息

    # 规格表管理
    url(r'^goods/specs/$', SpecsViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^goods/specs/(?P<pk>\d+)/$', SpecsViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),

    # 规格选项表管理
    url(r'^specs/options/$', OptionVIewSet.as_view({"get": "list", "post": "create"})),
    url(r'^specs/options/(?P<pk>\d+)/$', OptionVIewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    url(r'^goods/specs/simple/$', SpecSimpleListAPIView.as_view()),  # 规格信息

    # 图片数据管理
    url(r'^skus/images/$', ImageViewSet.as_view({"get": "list", "post": "create"})),
    url(r'^skus/images/(?P<pk>\d+)/$', ImageViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),
    url(r'^skus/simple/$', SKUSimpleListAPIView.as_view()),  # sku信息

]

# 视图集实现路由分发
router = SimpleRouter()
router.register(prefix='statistical', viewset=HomeViewSet, base_name='home')
urlpatterns += router.urls