import os
import time

from django.conf import settings
from django.template import loader

from contents.models import ContentCategory
from contents.utils import get_categories


def generate_static_index_html():
    """
    生成静态的主页html文件
    """
    print('%s: generate_static_index_html' % time.ctime())

    # 定义一个空的大字典用来包装所有广告数据
    # {'index_lbt': [], 'index_kx': []}
    contents = {}
    # 查询所有广告分类数据
    content_cat_qs = ContentCategory.objects.all()
    # 遍历广告类别查询集
    for content_cat in content_cat_qs:
        contents[content_cat.key] = content_cat.content_set.filter(status=True).order_by('sequence')

    context = {
        'categories': get_categories(),  # 商品分类
        'contents': contents  # 广告分类
    }

    # 获取首页模板文件
    template = loader.get_template('index.html')
    # 渲染首页html字符串
    html_text = template.render(context)
    # 将首页html字符串写入到指定目录，命名'index.html'
    file_path = os.path.join(settings.STATICFILES_DIRS[0], 'index.html')
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_text)