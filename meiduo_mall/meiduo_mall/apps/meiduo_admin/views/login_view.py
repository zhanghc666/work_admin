
from rest_framework.views import APIView
from rest_framework.response import Response

from meiduo_admin.serializers.login_serializer import LoginSerializer


class LoginAPIview(APIView):

    def post(self, request):
        # 1.获取前端传值
        # 2.创建序列化器对象
        serializer = LoginSerializer(data=request.data)
        # 3.进行校验
        serializer.is_valid(raise_exception=True)
        # 4.返回数据
        return Response({
            "username": serializer.validated_data["user"].username,
            "user_id": serializer.validated_data["user"].id,
            "token": serializer.validated_data["token"]
        })