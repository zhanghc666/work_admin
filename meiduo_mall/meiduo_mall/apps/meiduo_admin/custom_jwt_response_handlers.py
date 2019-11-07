def jwt_response_payload_handler(token, user=None, request=None):
    """
    自定义响应数据构造函数，以符合接口要求
    """

    return {
        'token': token,
        'user_id': user.id,
        'username': user.username
    }