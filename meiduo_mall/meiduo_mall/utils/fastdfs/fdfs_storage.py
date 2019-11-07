# from django.conf import settings
# from django.core.files.storage import Storage
#
#
# class FastDFSStorage(Storage):
#     """自定义文件存储系统，修改存储的方案"""
#     def __init__(self, fdfs_base_url=None):
#         """
#         构造方法，可以不带参数，也可以携带参数
#         :param base_url: Storage的IP
#         """
#
#     def _open(self, name, mode='rb'):
#         """
#         当打开要上传的文件时就会调用此方法
#         :param name: 要打开的文件/图片名
#         :param mode: 打开模式 只读二进制
#         :return:
#         """
#
#     def _save(self, name, content):
#         """
#         当上传图片时就会调用此方法
#         :param name: 要上传的文件名
#         :param content: 读取出来的途判文件bytes类型数据
#         :return: file_id
#         """
#
#     def exists(self, name):
#         """
#         当上传图片时就会调用此方法,只有图片没有存储过，才会上传
#         :param name: 要上传的图片名
#         :return: True or False
#         """
#
#
#     def url(self, name):
#         """
#         当在image属性后面调用它的url属性时就会自动来调用此方法,获取到图片的绝对路径
#         :param name: file_id
#         :return: 'http://192.168.103.210:8888' + file_id
#         """
#         # url = 'http://192.168.103.210:8888/' + name
#         url = settings.FDFS_BASE_URL + name
#         return url
from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client
from django.conf import settings


class CustomStorageSaveError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg



class FastDFSStorage(Storage):
    def _open(self, name, mode='rb'):
        """
        开打本地文件，保存
        :param name: 本地文件名
        :param mode:
        :return:
        """

        # 没有本地文件打开
        return None

    def _save(self, name, content, max_length=None):
        """
        保存逻辑
        :param name: 本地文件名或者上传来的文件名
        :param content: 上传来的文件对象
        :param max_length:
        :return: 文件名（保存到mysql数据库中）
        """
        # 补充上传fdfs的逻辑

        conn = Fdfs_client(settings.FDFS_CONF_PATH)
        res = conn.upload_by_buffer(content.read())
        if res is None:
            raise CustomStorageSaveError("自定义存储器上传失败！")

        image_id = res['Remote file_id']

        return image_id

    def url(self, name):
        # http://192.168.203.151:8888/group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429
        url = settings.FDFS_BASE_URL + name
        return url


    def exists(self, name):
        """
        判断文件是否已经被上传了
        :param name: 文件的名字
        :return: True or False
        """
        # 统一返回False，不做本地文件是否已经保存的判断
        return False
