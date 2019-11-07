from fdfs_client.client import Fdfs_client


# 创建fastDFS客户端
fast_client = Fdfs_client('client.conf')

# 上传图片
ret = fast_client.upload_by_filename('/home/python/Desktop/timg.jpeg')
# f = open('/home/python/Desktop/timg.jpeg', 'rb')

# content = f.read()
# ret = fast_client.append_by_buffer(content)
print(ret)