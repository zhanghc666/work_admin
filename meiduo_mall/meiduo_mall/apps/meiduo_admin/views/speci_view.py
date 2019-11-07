from rest_framework.viewsets import ModelViewSet

from meiduo_admin.serializers.speci_serializer import *
from meiduo_admin.pages import MyPage


class SpecsViewSet(ModelViewSet):
    """规格表列表数据"""
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecsModelSerializer
    pagination_class = MyPage

