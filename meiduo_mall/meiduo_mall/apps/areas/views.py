from django.shortcuts import render
from django.views import View
from django import http
from django.core.cache import cache

from .models import Area
from meiduo_mall.utils.response_code import RETCODE

# Create your views here.

class AreaView(View):
    """省市区查询"""
    def get(self, request):
        # 1.接收参数
        area_id = request.GET.get('area_id')

        # 2.根据有没有area_id查询参数来区分是查询所有省,还是指定area_id的下级所有行政区
        if area_id is None:
            # 先尝试从缓存中获取所有省数据
            # province_list = cache.get('province_list')
            province_list = None
            # 判断是否获取到缓存数据
            if province_list is None:
                # 查询所有省信息
                provinces_qs = Area.objects.filter(parent=None)
                province_list = []  # 用来装所有的省字典数据
                for provinces_model in provinces_qs:
                    province_list.append({
                        'id': provinces_model.id,
                        'name': provinces_model.name
                    })
                    # 从mysql查询完数据后，将它缓存到redis中
                cache.set('province_list', province_list, 60*60)
            return http.JsonResponse({'province_list': province_list, 'code': RETCODE.OK, 'errmsg': '所有省数据'})
        else:
            # 先从缓存中获取数据
            sub_data = cache.get('area_id%s' % area_id)
            if sub_data is None:
                # 查询指定area_id的下级所有行政区
                try:
                    # 查询指定area_id所对应的行政区
                    parent = Area.objects.get(id=area_id)
                    # 将area_id的下级行政区找出来
                    sub_qs = parent.subs.all()
                    # 定义一个列表用来包装所有下级行政区字典数据
                    sub_list = []
                    for sub_model in sub_qs:
                        sub_list.append({
                            'id': sub_model.id,
                            'name': sub_model.name
                        })
                    # 包装传给前端的大字典
                    sub_data = {
                        'id': parent.id,
                        'name': parent.name,
                        'subs': sub_list
                    }
                    # 设置缓存
                    cache.set('area_id%s' % area_id, sub_data, 60*60)
                except Area.DoesNotExist:
                    return  http.HttpResponseForbidden('area_id不存在')
            # 响应
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
