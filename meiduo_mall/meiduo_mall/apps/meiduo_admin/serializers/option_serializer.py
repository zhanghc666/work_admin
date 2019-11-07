from rest_framework import serializers

from goods.models import *


class OptionModelSerializer(serializers.ModelSerializer):
    """规格选项表列表数据 模型序列化器"""
    spec = serializers.StringRelatedField()
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = [
            "id",
            "value",
            "spec",
            "spec_id"
        ]