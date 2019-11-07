from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from meiduo_admin.serializers.sku_serializer import *
from meiduo_admin.pages import MyPage


class SKUViewSet(ModelViewSet):
    """SKU商品信息视图"""
    queryset = SKU.objects.all()
    serializer_class = SKUModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()


class GoodsCategoryView(ListAPIView):
    """三级分类信息"""
    queryset = GoodsCategory.objects.all()
    serializer_class = GoodsCategoryModelSerializer

    def get_queryset(self):
        return self.queryset.filter(parent_id__gt=37)


class SPUSimpleView(ListAPIView):
    """spu表名称数据"""
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer


class SpecOptView(ListAPIView):
    """SPU商品规格信息"""
    queryset = SPUSpecification.objects.all()
    serializer_class = SPUSpecSerializer

    def get_queryset(self):
        return self.queryset.filter(spu_id=self.kwargs.get("pk"))