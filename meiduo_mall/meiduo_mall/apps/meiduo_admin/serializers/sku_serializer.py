from rest_framework import serializers

from goods.models import *


class SKUSpecModelSerializer(serializers.ModelSerializer):
    """SKU具体规格,中间表 模型序列化器"""

    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification

        fields = ["spec_id", "option_id"]


class SKUModelSerializer(serializers.ModelSerializer):
    """SKU模型序列化器"""

    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    specs = SKUSpecModelSerializer(many=True)

    class Meta:
        model = SKU
        fields = "__all__"

    def create(self, validated_data):
        specs = validated_data.pop("specs")

        # 新建sku对象
        sku = super().create(validated_data)

        for sp in specs:
            sp["sku_id"] = sku.id
            SKUSpecification.objects.create(**sp)

        return sku

    def update(self, instance, validated_data):
        # 1、提取前端传值（新的规格选项  specs）
        specs = validated_data.pop('specs')
        # 2、删除中间表原有的记录
        SKUSpecification.objects.filter(sku_id=instance.id).delete()

        # 3.3、插入新的规格和选项中间表数据
        for sp in specs:
            sp["sku_id"] = instance.id
            SKUSpecification.objects.create(**sp)

        instance = super().update(instance, validated_data)

        return instance


class GoodsCategoryModelSerializer(serializers.ModelSerializer):
    """商品类别 模型序列化器"""

    class Meta:
        model = GoodsCategory
        fields = ["id", "name"]


class SPUSimpleSerializer(serializers.ModelSerializer):
    """spu表名称数据 模型序列化器"""

    class Meta:
        model = SPU
        fields = ["id", "name"]


class SpecOptSerializer(serializers.ModelSerializer):
    """规格选项 模型序列化器"""

    class Meta:
        model = SpecificationOption
        fields = ["id", "value"]


class SPUSpecSerializer(serializers.ModelSerializer):
    """SPU商品规格信息 模型序列化器"""
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    options = SpecOptSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = [
            "id",
            "name",
            "spu",
            "spu_id",
            "options"
        ]

