class Route:
    """
    路由装饰器，该类的实例即为路由装饰器
    """

    def __init__(self, app):
        self.app = app

    def __call__(self, url, **options):
        # 若 methods 参数没有定义，则初始化仅支持 GET 方法
        if 'methods' not in options:
            options['methods'] = ['GET']

        def decorator(f):
            # 调用应用内部的 add_url_rule 添加规则
            self.app.add_url_rule(url, f, 'route', **options)
            return f

        return decorator
