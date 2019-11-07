from rest_framework import serializers
from django.contrib.auth.hashers import make_password

from users.models import User


class UserModelSerializer(serializers.ModelSerializer):

    class Meta:
        model = User

        fields = [
            'id',
            'username',
            'mobile',
            'email',
            'password'
        ]

        extra_kwargs = {
            "password": {"write_only": True}  # password只作用于反序列化
        }

    def validate(self, attrs):

        attrs['is_staff'] = True  # 默认创建超级管理员权限
        attrs['password'] = make_password(attrs['password'])  # 利用自带的加密给密码加密

        return attrs

    # def create(self, validated_data):
    #     """
    #     默认的ModelSerializer.create无法完成，1、密码加密，2、创建的用户是普通用户
    #     """
    #     return User.objects.create_superuser(**validated_data)