from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^list/(?P<category_id>\d+)/(?P<page_num>\d+)/$', views.ListView.as_view(), name='list'),  # 商品列表界面

    url(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),  # 热销排行

    url(r'^detail/(?P<sku_id>\d+)/$', views.DetailView.as_view()),  # 商品详情

    url(r'^visit/(?P<category_id>\d+)/$', views.DetailVisitView.as_view()),  # 商品类别访问量统计

    url(r'^orders/info/(?P<page_num>\d+)/$', views.AllOrders.as_view()),  # 全部订单

]