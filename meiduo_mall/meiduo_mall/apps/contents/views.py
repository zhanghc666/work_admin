from django.shortcuts import render
from django.views import View

from .models import Content, ContentCategory
from goods.models import GoodsCategory, GoodsChannel
from .utils import get_categories

class IndexView(View):
    """首页"""
    def get(self, request):

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

        return render(request, 'index.html', context)