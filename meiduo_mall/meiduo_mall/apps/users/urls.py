from django.conf.urls import url
from django.contrib import admin
from . import views

urlpatterns = [
    url(r"^register/$", views.RegisterView.as_view(), name="refister"),

    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),  # 用户是否重复

    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),  # 手机号是否重复

    url(r'^login/$', views.LoginView.as_view()),  # 用户登陆

    url(r'logout/$', views.LogoutView.as_view()),  # 用户退出

    url(r'info/$', views.InfoView.as_view()),  # 用户中心

    url(r'emails/$', views.EmailView.as_view()),  # 邮箱验证

    url(r'^emails/verification/$', views.EmailVerifyView.as_view()),  # 激活邮箱

    url(r'^addresses/$', views.AddressView.as_view()),  # 收货地址

    url(r'^addresses/create/$', views.AddressCreateView.as_view()),  # 新增收获地址

    url(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),  # 修改和删除收货地址

    url(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),  # 修改默认收货地址

    url(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateAddressTitleView.as_view()),  # 修改默认收货地址

    url(r'^password/$', views.ChangePasswordView.as_view()),  # 修改用户密码

    url(r'^browse_histories/$', views.UserBrowseHistory.as_view()),  # 商品浏览记录

    # url(r'^find_password/$', views.FindPassword.as_view()),  # 找回密码界面
    #
    # url(r'^/accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/sms/token/', views.InputID.as_view())  # 输入用户名第一步




    url(r'^find_password/$', views.Find_Password.as_view(), name='find_password'),

    # accounts /python/sms/token/?text=fkhs & image_code_id=89
    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/sms/token/$', views.Find_Password_Username.as_view()),

    # 动态验证码已经被之前路径截取
    # url(r'^sms_codes/', views.Find_Password_SMS.as_view()),
    # accounts/python/password/token/?sms_code=248861
    url(r'^sms_codes/$', views.Create_SMS.as_view()),

    url(r'^accounts/(?P<username>[a-zA-Z0-9_-]{5,20})/password/token/$', views.Find_Password_SMS.as_view()),

    url(r'^users/(?P<user_id>\d+)/password/$', views.Find_Password_Reset.as_view()),

]
