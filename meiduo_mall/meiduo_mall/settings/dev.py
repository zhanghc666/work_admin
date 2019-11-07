

# 开发使用的配置

"""
Django settings for meiduo_mall project.

Generated by 'django-admin startproject' using Django 1.11.11.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.11/ref/settings/
"""

import os
import sys
# Build paths inside the project like this: os.path.join(BASE_DIR, ...)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.11/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vldh_sigqe-d+3bw-mz=2zhnny&xj=en+aoby5*xx1g&sf44@)'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


sys.path.insert(0, os.path.join(BASE_DIR, "apps"))

# 允许哪些域名能访问django
ALLOWED_HOSTS = ['www.meiduo.site', '127.0.0.1']
# ALLOWED_HOSTS = ['127.0.0.1']


# Application definition
# 什么时候必须注册应用：如果应用中定义的模型需要迁移建表和使用django模板进行自定义过滤器时才必须要注册应用，其他情况，可以不注册
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'haystack', # 全文检索
    'django_crontab', # 定时任务
    'corsheaders',

    'users.apps.UsersConfig',  # 用户模块
    'oauth.apps.OauthConfig',  # QQ模块
    'areas.apps.AreasConfig',  # 省市区模块
    'contents.apps.ContentsConfig',  # 广告模块
    'goods.apps.GoodsConfig',  # 商品模块
    'orders.apps.OrdersConfig',  # 订单模块
    'payment.apps.PaymentConfig',  # 支付模块

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'meiduo_mall.urls'

# TEMPLATES = [
#     {
#         'BACKEND': 'django.template.backends.django.DjangoTemplates',
#         'DIRS': [],
#         'APP_DIRS': True,
#         'OPTIONS': {
#             'context_processors': [
#                 'django.template.context_processors.debug',
#                 'django.template.context_processors.request',
#                 'django.contrib.auth.context_processors.auth',
#                 'django.contrib.messages.context_processors.messages',
#             ],
#         },
#     },
# ]

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.jinja2.Jinja2',  # jinja2模板引擎
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            # 补充Jinja2模板引擎环境
            'environment': 'meiduo_mall.utils.jinja2_env.jinja2_environment',
        },
    },
]


WSGI_APPLICATION = 'meiduo_mall.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, '../../db.sqlite3'),
#     }
# }


DATABASES = {
    'default': {  # 主机: 写
        'ENGINE': 'django.db.backends.mysql', # 数据库引擎
        'HOST': '127.0.0.1', # 数据库主机
        'PORT': 3306, # 数据库端口
        'USER': 'root', # 数据库用户名
        'PASSWORD': 'mysql', # 数据库用户密码
        'NAME': 'meiduo_mall' # 数据库名字
    },
    # 'slave': {  # 从机: 读
    #     'ENGINE': 'django.db.backends.mysql',  # 数据库引擎
    #     'HOST': '127.0.0.1',  # 数据库主机
    #     'PORT': 8306,  # 数据库端口
    #     'USER': 'root',  # 数据库用户名
    #     'PASSWORD': 'mysql',  # 数据库用户密码
    #     'NAME': 'meiduo_mall'  # 数据库名字
    # },
    #
}

# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

# LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'zh-Hans'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True
# USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

STATIC_URL = '/static/'

# 配置静态文件加载路径
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]


# 项目的缓存配置
CACHES = {
    "default": { # 默认
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "session": { # session
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "verify_codes": {  # 验证码
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/2",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "history": {  # 浏览记录
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/3",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
    "carts": {  # 购物车
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/4",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}

# session存储配置
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "session"


# 日志输出器配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # 是否禁用已经存在的日志器
    'formatters': {  # 日志信息显示的格式
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(lineno)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'filters': {  # 对日志进行过滤
        'require_debug_true': {  # django在debug模式下才输出日志
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {  # 日志处理方法
        'console': {  # 向终端中输出日志
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {  # 向文件中输出日志
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(os.path.dirname(BASE_DIR), 'logs/meiduo.log'),  # 日志文件的位置
            'maxBytes': 300 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose'
        },
    },
    'loggers': {  # 日志器
        'django': {  # 定义了一个名为django的日志器
            'handlers': ['console', 'file'],  # 可以同时向终端与文件中输出日志
            'propagate': True,  # 是否继续传递日志信息
            'level': 'INFO',  # 日志器接收的最低日志级别
        },
    }
}

# 修改认证用户模型类
# String model references must be of the form 'app_label.ModelName'.
AUTH_USER_MODEL = 'users.User'

# 修改django自定义后端
# AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']
AUTHENTICATION_BACKENDS = ['users.utils.UsernameMobileAuthBackend']

# 修改登录路由
LOGIN_URL = '/login/'


# QQ登录配置项
QQ_CLIENT_ID = '101518219'
QQ_CLIENT_SECRET = '418d84ebdc7241efb79536886ae95224'
QQ_REDIRECT_URI = 'http://www.meiduo.site:8000/oauth_callback'


# 发邮箱的配置信息(我的)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 指定邮件后端
# EMAIL_HOST = 'smtp.163.com'  # 发邮件主机
# EMAIL_PORT = 25  # 发邮件端口
# EMAIL_HOST_USER = 'zhang1076727931@163.com'  # 授权的邮箱
# EMAIL_HOST_PASSWORD = 'zhang064217'  # 邮箱授权时获得的密码，非注册登录密码
# EMAIL_FROM = '一个幽默风趣的小哥哥<zhang1076727931@163.com>'  # 发件人抬头

# 发邮箱的配置信息
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # 指定邮件后端
EMAIL_HOST = 'smtp.163.com'  # 发邮件主机
EMAIL_PORT = 25  # 发邮件端口
EMAIL_HOST_USER = 'itcast99@163.com'  # 授权的邮箱
EMAIL_HOST_PASSWORD = 'python99'  # 邮箱授权时获得的密码，非注册登录密码
EMAIL_FROM = '美多商城<itcast99@163.com>'  # 发件人抬头
# 邮箱验证链接
EMAIL_VERIFY_URL = 'http://www.meiduo.site:8000/emails/verification/'

# APPEND_SLASH = False

# MEDIA_URL = 'http://192.168.75.128:8888/'

# FASTDFS下载图片的url
FDFS_BASE_URL = 'http://image.meiduo.site:8888/'

# 指定自定义的Django文件存储类
DEFAULT_FILE_STORAGE = 'meiduo_mall.utils.fastdfs.fdfs_storage.FastDFSStorage'


# Haystack
HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.elasticsearch_backend.ElasticsearchSearchEngine',
        'URL': 'http://192.168.75.128:9200/',  # Elasticsearch服务器ip地址，端口号固定为9200
        'INDEX_NAME': 'meiduo_mall',  # Elasticsearch建立的索引库的名称
    },
}

# 当添加、修改、删除数据时，自动生成索引
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# 指定搜索商品的分页
HAYSTACK_SEARCH_RESULTS_PER_PAGE = 2


# 支付宝
ALIPAY_APPID = '2016091900551154'
# ALIPAY_APPID = '2016101300677679'  # 我的
ALIPAY_DEBUG = True  # 表示是沙箱环境还是真实支付环境
ALIPAY_URL = 'https://openapi.alipaydev.com/gateway.do'
ALIPAY_RETURN_URL = 'http://www.meiduo.site:8000/payment/status/'


# 定时器任务
CRONJOBS = [
    # 每1分钟生成一次首页静态文件
    ('*/1 * * * *', 'contents.crons.generate_static_index_html', '>> ' + os.path.join(os.path.dirname(BASE_DIR), 'logs/crontab.log'))
]

CRONTAB_COMMAND_PREFIX = 'LANG_ALL=zh_cn.UTF-8'


# 指定Mysql路由
# DATABASE_ROUTERS = ['meiduo_mall.utils.db_router.MasterSlaveDBRouter']

# 微博登录配置项,  这些要去微博开发者账号wj0102198@sina.cn里拿到的数据
WEIBO_CLIENT_ID = '3609480874'
WEIBO_CLIENT_SECRET = 'e727b6b87c873b37453b15f877345a6f'
WEIBO_REDIRECT_URI = 'http://www.meiduo.site:8000/sina_callback'


# corsheader旧版本，不要求写入协议； 新版要求写如协议
CORS_ORIGIN_WHITELIST = (
    # "http://127.0.0.1:8080", # 新版
    "http://127.0.0.1:8080", # 旧版
    "http://www.meiduo.site:8000", # 旧版
)


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # jwt认证机制
        # 会在请求头中提取Authorization记录的token值，进行数据完整性校验
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ),

}

import datetime
JWT_AUTH = {
    'JWT_EXPIRATION_DELTA': datetime.timedelta(days=1),
    # 自定义构造响应数据函数
    'JWT_RESPONSE_PAYLOAD_HANDLER': 'meiduo_admin.custom_jwt_response_handlers.jwt_response_payload_handler',

}


# fafs文件上传路径
FDFS_CONF_PATH = os.path.join(BASE_DIR, 'utils/fastdfs/client.conf')