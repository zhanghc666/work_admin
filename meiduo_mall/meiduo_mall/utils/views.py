from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View


class LoginRequiredView(LoginRequiredMixin, View):
    """判断登录视图基类"""
    pass