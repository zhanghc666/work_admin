# 定义一个序列化器。
# 完成：用户名和密码校验，token的签发

from rest_framework import serializers
from rest_framework_jwt.utils import jwt_payload_handler, jwt_encode_handler

from users.views import authenticate


class LoginSerializer(serializers.Serializer):
    """用户登录"""
    username = serializers.CharField(write_only=True, required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        # 1.身份认证
        user = authenticate(username=attrs.get('username'), password=attrs.get('password'))
        if not user:
            return serializers.ValidationError("用户名或密码错误")

        # 2.token签发
        payload = jwt_payload_handler(user)
        token = jwt_encode_handler(payload)

        # 3.返回有效数据
        return {
            "user": user,
            "token": token
        }