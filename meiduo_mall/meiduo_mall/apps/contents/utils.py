from goods.models import GoodsChannel


def get_categories():
    # 1.包装首页商品分类数据
    # 定义用来包装商品类别数据的大字典
    categories = {}

    # 查询所有商品频道数据
    goods_channel_qs = GoodsChannel.objects.order_by('group_id', 'sequence')

    # 遍历商品类别查询集
    for goods_channel in goods_channel_qs:
        group_id = goods_channel.group_id

        if group_id not in categories:
            categories[group_id] = {
                'channels': [],  # 一级标题
                'sub_cats': []  # 二级标题及其所有对应的三级标题
            }

        # 获取当前的一级类别
        cat1 = goods_channel.category
        # 给一级类别多定义一个url属性用来记录它自己的链接
        cat1.url = goods_channel.url
        # 将准备好的一级类别添加到当前组的channels key对应的列表中
        categories[group_id]['channels'].append(cat1)

        # 查询当前一级下的所有二级
        cat2_qs = cat1.subs.all()
        # 遍历二级类别查询集,给每一个二级类型多一定一个属性用来记录它下面的所有三级
        for cat2 in cat2_qs:
            # 查询当前二级下的所有三级
            cat3_qs = cat2.subs.all()
            # 将当前二级下的所有三级记录到二级的sub_cats属性上
            cat2.sub_cats = cat3_qs
            # 将每个准备好的二级添加到每组的列表中
            categories[group_id]['sub_cats'].append(cat2)

    return categories