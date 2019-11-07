from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from meiduo_admin.serializers.spu_serializer import *
from meiduo_admin.pages import MyPage
from meiduo_admin.serializers.sku_serializer import *


class SPUViewSet(ModelViewSet):
    """SPU表列表数据"""
    queryset = SPU.objects.all()
    serializer_class = SPUModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        keyword = self.request.query_params.get("keyword")
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()


class BrandSimpleView(ListAPIView):
    """品牌数据"""
    queryset = Brand.objects.all()
    serializer_class = BrandSimpleSerializer


class GoodsCategoriteView(ListAPIView):
    """一级,二级，三级分类信息"""
    queryset = GoodsCategory.objects.all()
    serializer_class = GoodsCategoryModelSerializer

    def get_queryset(self):
        pk = self.kwargs.get('pk')
        if pk:
            return self.queryset.filter(parent_id=pk)

        return self.queryset.filter(parent_id=None)

