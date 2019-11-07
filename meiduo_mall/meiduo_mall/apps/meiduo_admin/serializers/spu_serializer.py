from rest_framework import serializers

from goods.models import *


class SPUModelSerializer(serializers.ModelSerializer):
    """SPU表列表数据 模型序列化器 """
    brand = serializers.StringRelatedField()
    brand_id = serializers.IntegerField()
    category1_id = serializers.IntegerField()
    category2_id = serializers.IntegerField()
    category3_id = serializers.IntegerField()

    class Meta:
        model = SPU
        # fields = "__all__"

        exclude = [
            "category1",
            "category2",
            "category3"
        ]


class BrandSimpleSerializer(serializers.ModelSerializer):
    """品牌数据 模型序列化器"""

    class Meta:
        model = Brand
        fields = ["id", "name"]