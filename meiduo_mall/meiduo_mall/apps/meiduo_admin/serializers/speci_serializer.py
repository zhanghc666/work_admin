from rest_framework import serializers

from goods.models import *


class SpecsModelSerializer(serializers.ModelSerializer):
    """规格表列表数据 模型序列化器"""
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()

    class Meta:
        model = SPUSpecification
        fields = [
            "id",
            "name",
            "spu",
            "spu_id"
        ]


