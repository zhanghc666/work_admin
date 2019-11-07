

from rest_framework.generics import ListAPIView, CreateAPIView

from users.models import *
from meiduo_admin.serializers.user_serializer import *
from meiduo_admin.pages import MyPage


class UserAPIView(ListAPIView, CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        # 获得后续序列化操作的数据集
        # 介入，进行过滤
        # 如果查询字符串中keyword，根据该数据进行过滤
        # 如果没有默认返回所有
        # 查询字符串参数，request.query_params.get("keyword")
        keyword = self.request.query_params.get("keyword", None)
        if keyword:
            return self.queryset.filter(username__contains=keyword, is_staff=True)
        # is_staff=True：返回超级管理员用户
        return self.queryset.filter(is_staff=True)