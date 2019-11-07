from django.db import models
from meiduo_mall.utils.models import BaseModel
from users.models import User

class OAuthQQUser(BaseModel):
    """QQ登录用户数据"""
    # user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_qq'
        verbose_name = 'QQ登录用户数据'
        verbose_name_plural = verbose_name



class OAuthWEIBOUser(BaseModel):
    """微博登录用户数据"""                     # 关联  主表删除则字表随删
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, verbose_name='用户')
    openid = models.CharField(max_length=64, verbose_name='openid', db_index=True)

    class Meta:
        db_table = 'tb_oauth_weibo'
        verbose_name = 'WEIBO登录用户数据'
        verbose_name_plural = verbose_name

