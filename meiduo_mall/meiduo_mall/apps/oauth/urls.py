from django.conf.urls import url
from . import views

urlpatterns = [

    url(r'^qq/authorization/$', views.OAuthQQURLView.as_view()),  # 获取QQ登录url

    url(r'^oauth_callback/$', views.OAuthQQView.as_view()),  # QQ登录成功回调处理

    url(r'^weibo/authorization/', views.OAuthWeiboURLView.as_view()),  # 获取weibo登录url

    url(r'^sina_callback/$', views.OAuthWeiboView.as_view()),  # weibo登录成功回调处理

]