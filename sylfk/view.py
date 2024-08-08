class View:
    """
    视图类的基类
    """

    methods = []  # 支持的请求方法列表
    methods_meta = {}  # 请求方法与对应的方法的映射

    def dispatch_request(self, request, *args, **options):
        """
        视图处理函数调度入口，子类需定义次方法
        """
        raise NotImplementedError

    @classmethod
    def get_func(cls, name):
        """
        创建视图函数，参数 name 就是函数名
        """
        def func(*args, **kw):
            # 通过视图对象调用处理函数调度入口，返回视图处理结果
            return cls().dispatch_request(*args, **kw)

        # 为视图函数绑定属性
        func.__name__ = name
        func.__doc__ = cls.__doc__
        func.__module__ = cls.__module__
        func.methods = cls.methods

        return func


class Controller:
    """
    控制器类，该类的实例有点像蓝图，至少在创建节点字符串时作用是相似的
    """

    def __init__(self, name, url_map):
        # 控制器名字，生成节点时会用到，为了区分不同控制器下同名的视图对象
        self.name = name
        # 存放映射关系的列表，列表中的元素是字典
        self.url_map = url_map
