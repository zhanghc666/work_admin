from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^image_codes/(?P<uuid>[\w-]+)/$", views.ImageCodeView.as_view()),  # 图形验证码
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view()),  # 短信验证码

]