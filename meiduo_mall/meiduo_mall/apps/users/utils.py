from django.contrib.auth.backends import ModelBackend
import  re
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData

from .models import User


def get_user_account(account):
    """
    通过用户名/手机号获取suer
    :param account:
    :return:
    """
    try:
        if re.match(r"^1[3-9]]\d{9}$", account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None

    return user

class UsernameMobileAuthBackend(ModelBackend):
    """自定义认证登录认证后端类"""

    def authenticate(self, request, username=None, password=None, **kwargs):
        # 1.根据用户名手机号动态查询user
        user = get_user_account(username)

        # 判断该登录请求是否是后台管理站点登录
        if request is None:
            # 如果是管理站点登录，权限必须是is_staff=True
            if not user.is_staff:
                return None  # 身份认证失败

        # 2.判断密码是否正确，正确返回user
        if user and user.check_password(password):
            return user

def generate_verify_email_url(user):
    """
    生成邮箱激活url
    :param user: 要激活邮箱的用户模型对象
    :return: 邮箱激活url
    """
    serializer = Serializer(secret_key=settings.SECRET_KEY,expires_in=60*60*24)
    data = {'user_id':user.id, 'email':user.email}
    token = serializer.dumps(data).decode()
    # verify_url = 'http://www.meiduo.site:8000/emails/verification/' + '?token=' + 'xxx'
    verify_url = settings.EMAIL_VERIFY_URL + '?token=' + token
    return verify_url

def get_token_user(token):
    """通过token进行解密并获取到user
    token要解密的用户唯一信息
    """
    serializer = Serializer(secret_key=settings.SECRET_KEY,expires_in=60*60*24)
    try:  # 解密可能会失败，所以用try
        data = serializer.loads(token)
        user_id = data.get('user_id')
        email = data.get('email')
        user = User.objects.get(id=user_id, email=email)
        return user
        # try:
        #     user = User.objects.get(id=user_id, email=email)
        #     return user
        # except User.DoesNotExist:
        #     return None
    except BadData:
        return None