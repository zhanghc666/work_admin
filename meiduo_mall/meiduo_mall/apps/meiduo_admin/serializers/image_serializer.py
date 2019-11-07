from rest_framework import serializers

from goods.models import *


class ImageModelSerializer(serializers.ModelSerializer):
    """图片列表数据 模型序列化器"""
    # PrimaryKeyRelatedField: 作用于反序列化的时候。需要指明queryset过滤集
    sku = serializers.PrimaryKeyRelatedField(queryset=SKU.objects.all())

    class Meta:
        model = SKUImage
        fields = [
            "id",
            "sku",
            "image"
        ]

    # def validate(self, attrs):
    #     """
    #     处理文件类型数据，默认create和update方法无法帮助我们上传fdfs操作
    #     默认指明的后端存储器。无法完成上传操作！
    #
    #     attrs['image'] = <文件对象>
    #     """
    #     # 手动完成图片类型数据上传fdsfs
    #
    #     image_obj = attrs.pop('image') # 文件对象
    #     # 1、提取文件对象中的文件数据（字节）
    #     content = image_obj.read() # bytes
    #     # 2、上传fdfs
    #     conn = Fdfs_client(settings.FDFS_CONF_PATH)
    #     res = conn.upload_by_buffer(content)
    #     # {
    #     #     'Group name': group_name,
    #     #     'Remote file_id': remote_file_id,
    #     #     'Status': 'Upload successed.',
    #     #     'Local file name': '',
    #     #     'Uploaded size': upload_size,
    #     #     'Storage IP': storage_ip
    #     # } if success else None
    #
    #     if res is None:
    #         # 上传失败了
    #         return serializers.ValidationError("图片上传失败！")
    #
    #     # 3、成功后，拿到文件的唯一标示
    #     image_id = res['Remote file_id']
    #
    #     # 4、文件的标示记录在mysql中
    #     # attrs['image'] = '/group/sss/fewfe/grwgr....'
    #     attrs['image'] = image_id
    #
    #     return attrs


class SKUImageModelSerializer(serializers.ModelSerializer):
    """sku表数据 模型序列化器"""

    class Meta:
        model = SKU
        fields = [
            "id",
            "name"
        ]