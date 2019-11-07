

def get_breadcrumb(cat3):
    """包装面包屑导航数据"""

    # 给cat1定义一个url
    cat1 = cat3.parent.parent
    cat1.url = cat1.channels.all()[0].url

    # 用来装面包屑数据
    breadcrumb = {
        'cat3': cat3,
        'cat2': cat3.parent,
        'cat1': cat1
    }

    return breadcrumb