


# 专门定义分页器
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MyPage(PageNumberPagination):
    page_query_param = "page" # ?page=xxx
    page_size_query_param = "pagesize" # ?pagesize=xxx
    page_size = 10
    max_page_size = 10

    # 修改分页器默认构建的响应结果
    def get_paginated_response(self, data):
        # data: 模型类分页的子集
        # return: 响应结果(数据格式)
        return Response({
            "counts": self.page.paginator.count,
            "lists": data,
            "page": self.page.number,
            "pages": self.page.paginator.num_pages, # 总页数
            "pagesize": self.page_size,
        })