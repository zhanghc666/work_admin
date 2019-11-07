from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListAPIView

from meiduo_admin.serializers.image_serializer import *
from meiduo_admin.pages import MyPage


class ImageViewSet(ModelViewSet):
    """图片列表数据"""
    queryset = SKUImage.objects.all()
    serializer_class = ImageModelSerializer
    pagination_class = MyPage


class SKUSimpleListAPIView(ListAPIView):
    """sku表数据"""
    queryset = SKU.objects.all()
    serializer_class = SKUImageModelSerializer