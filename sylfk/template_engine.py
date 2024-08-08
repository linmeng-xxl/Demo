import os
import re

# 模板标记
pattern = r'{{(.*?)}}'


def parse_args(obj):
    """
    解析模板
    """
    comp = re.compile(pattern)  # 创建匹配对象
    result = comp.findall(obj)  # 获取匹配结果

    return result or ()


def replace_template(app, path, **options):
    """
    置换函数，读取模板文件，替换变量
    :param app: 应用程序类
    :param path: 模板文件相对于 templates 的路径
    :param options: 参数字典
    """

    # 默认返回内容，当找不到本地模板文件时返回
    content = '<h1>Not Found Tmeplate.</h1>'
    # 获取模板文件本地路径
    path = os.path.join(app.template_folder, path)

    # 如果路径存在，则开始解析置换
    if os.path.exists(path):
        with open(path, 'rb') as f:
            content = f.read().decode()
        # 解析出所有的标记
        args = parse_args(content)
        # 如果置换内容不为空，开始置换
        if options:
            for arg in args:
                # 从标记中获取键
                key = arg.strip()
                # 如果键存在置换数据中，则进行数据替换，反之替换为空
                old_value = '{{{{{}}}}}'.format(arg)  # 等价于 {{ arg }}
                new_value = str(options.get(key, ''))
                content = content.replace(old_value, new_value)
    return content