from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadData
from django.conf import settings



def generate_openid_signature(openid):
    """
    对openid 进行加密
    :param openid: 要加密的数据
    :return: 加密后的openid
    """
    # 1.创建加密实例对象
    serializer = Serializer(secret_key=settings.SECRET_KEY,expires_in=600)
    # 2.包装需要加密的数据成 字典格式
    data = {'openid':openid}
    # 3.调用加密实例对象.dumps方法进行加密 ,加密后的数据默认是bytes类型
    token_bytes = serializer.dumps(data)  # 输出 序列化: 模型转字典
    # 4.把bytes类型转换成字符串
    return token_bytes.decode()


def generate_origin_openid(token):
    """
    对openid进行解密
    :param token: 要进行解密的openid
    :return: 原始openid
    """
    # 1.创建加密实例对象
    serializer = Serializer(secret_key=settings.SECRET_KEY,expires_in=600)
    # 2.调用loads方法进行解密
    try:
        data = serializer.loads(token)  # 输入 反序列化: 字典转模型
        return data.get('openid')
    except BadData:  # 如果解密失败返回None
        return None

