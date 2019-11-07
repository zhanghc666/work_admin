from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^orders/settlement/$', views.OrderSettlementView.as_view()),  # 去结算

    url(r'^orders/commit/$', views.OrderCommitView.as_view()),  # 提交订单

    url(r'^orders/success/$', views.OrderSuccessView.as_view()),  # 提交订单成功

    url(r'^orders/comment/$', views.GoodsComment.as_view()),  # 商品评价

    url(r'^comments/(?P<sku_id>\d+)/$', views.CommentView.as_view()),  # 商品评论展示

]