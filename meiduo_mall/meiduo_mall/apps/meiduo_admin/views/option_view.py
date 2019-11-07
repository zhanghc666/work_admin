from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from meiduo_admin.serializers.option_serializer import *
from meiduo_admin.serializers.speci_serializer import SpecsModelSerializer
from meiduo_admin.pages import MyPage


class OptionVIewSet(ModelViewSet):
    "规格选项表列表数据"
    queryset = SpecificationOption.objects.all()
    serializer_class = OptionModelSerializer
    pagination_class = MyPage


class SpecSimpleListAPIView(ListAPIView):
    """规格信息"""
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecsModelSerializer
