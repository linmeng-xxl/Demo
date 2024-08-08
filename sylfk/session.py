import base64
import os.path
import time
import os
import json


def create_session_id():
    """
    创建 Session ID （通常会存到客户端 Cookies 中的 session_id 中）
    """

    # 获取当前时间戳，转化为字符串，编码为二进制字符串
    # 使用 base64 加密后解码生成字符串，去掉最后两个字符 '=\n' 然后反转
    return base64.encodebytes(str(time.time()).encode()).decode()[:-2][::-1]


def get_session_id(request):
    """
    从请求中获取 Session ID
    """

    return request.cookies.get('session_id')


class Session:
    """
    会话类，该类的实例为全局对象
    """

    def __init__(self, session_path='session'):
        self.__session_map__ = {}  # 会话映射表
        self.__storage_path__ = session_path  # 会话本地存放路径
        if not os.path.exists(self.__storage_path__):
            os.makedirs(self.__storage_path__)

    def __new__(cls, *args, **kwargs):
        """
        单例模式，实现一个全局 Session 类的实例
        """
        if not hasattr(cls, '_Session__instance'):
            cls.__instance = super().__new__(cls, *args, **kwargs)
        return cls.__instance

    def push(self, request, item, value):
        """
        更新或添加会话
        """
        # 从请求中获取客户端的 Session ID
        session_id = get_session_id(request)

        # 如果这个 Session ID 已存在于映射表中，则直接为其添加新的数据键值对
        # 如果不存在，则先初始化为空的字典，再添加数据键值对
        if session_id in self.__session_map__:
            self.__session_map__[session_id][item] = value
        else:
            self.__session_map__[session_id] = {item: value}

        self.storage(session_id)

    def pop(self, request, item, value=True):
        """
        删除当前会话的某个字段
        """
        session_id = get_session_id(request)
        current_session = self.__session_map__.get(session_id, {})

        # 判断数据项的键是否存在于当前的会话中，如果存在则删除
        if item in current_session:
            current_session.pop(item)
            self.storage(session_id)

    def set_storage_path(self, session_path):
        """
        修改存放会话数据的目录
        """
        self.__storage_path__ = session_path
        if not os.path.exists(self.__storage_path__):
            os.makedirs(self.__storage_path__)

    def storage(self, session_id):
        """
        会话持久化
        """
        filename = os.path.join(self.__storage_path__, session_id)

        with open(filename, 'wb') as f:
            content = json.dumps(self.__session_map__.get(session_id))
            f.write(base64.encodebytes(content.encode()))

    def load_all_session(self):
        """
        加载本地文件中的会话数据
        """
        session_file_list = os.listdir(self.__storage_path__)

        for session_id in session_file_list:
            filename = os.path.join(self.__storage_path__, session_id)
            with open(filename, 'rb') as f:
                content = f.read()
            # 把文件内容进行 base64 解码
            content = base64.decodebytes(content)
            # 把 Session ID 与对应的会话内容绑定到回话映射表中
            self.__session_map__[session_id] = json.loads(content.decode())

    def get(self, request):
        """
        获取当前请求相关的会话数据
        """
        return self.__session_map__.get(get_session_id(request), {})

    def get_item(self, request, item):
        """
        获取当前请求相关的会话数据中的某个字段
        """
        return self.get(request).get(item, None)


class AuthSession:
    """
    效验基类
    """

    @classmethod
    def auth_session(cls, f, *args, **options):
        """
        效验装饰器
        """
        def decorator(obj, request):
            if cls.auth_logic(request, *args, **options):
                return f(obj, request)
            return cls.auth_fail_callback(request, *args, **options)

        return decorator

    @staticmethod
    def auth_logic(request, *args, **options):
        """
        逻辑验证的接口，返回一个布尔值
        """
        raise NotImplementedError

    @staticmethod
    def auth_fail_callback(request, *args, **options):
        """
        验证失败的回调接口
        """
        raise NotImplementedError


# 单例全局对象
session = Session()
