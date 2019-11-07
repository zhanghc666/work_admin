from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^carts/$', views.CartsView.as_view()),  # 购物车

    url(r'^carts/simple/$', views.CartsSimpleView.as_view()),  # 简单版购物车

    url(r'^carts/selection/$', views.CartsSelectedAllView.as_view()),  # 购物车全选

]