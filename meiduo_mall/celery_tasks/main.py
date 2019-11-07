# celery客户端及启动文件
from celery import Celery
import os

# 告诉celery它想要django配置文件在那里
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")


# 1.创建celery客户端对象
celery_app = Celery('meiduo')

# 2.加载celery配置信息
celery_app.config_from_object('celery_tasks.config')

# 3.指定celery可以生产什么文件
celery_app.autodiscover_tasks(['celery_tasks.sms', 'celery_tasks.email'])