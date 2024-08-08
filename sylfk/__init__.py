# 框架核心文件
import os

from werkzeug.serving import run_simple

from werkzeug.wrappers import Response

from sylfk.wsgi_adapter import wsgi_app

import sylfk.exceptions as exceptions

from sylfk.helper import parse_static_key

from sylfk.route import Route

from sylfk.template_engine import replace_template

from sylfk.session import create_session_id, session

import json


content_type = 'text/html; charset=UTF-8'

# 常见异常及其响应对象的映射关系
ERROR_MAP = {
    '2': Response('<h1>E2 Not Found File</h1>',
                  content_type=content_type, status=500),
    '13': Response('<h1>E13 No Read Permission</h1>',
                   content_type=content_type, status=500),
    '401': Response('<h1>401 Unknown or unsupported method.</h1>',
                    content_type=content_type, status=401),
    '404': Response('<h1>404 Source Not Found.</h1>',
                    content_type=content_type, status=404),
    '503': Response('<h1>503 Unknown function type.</h1>',
                    content_type=content_type, status=503),
}

# 文件类型及其代号的映射关系
TYPE_MAP = {
    'css': 'text/css',
    'js': 'text/css',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg'
}


# 处理函数数据结构
class ExecFunc:
    def __init__(self, func, func_type, **options):
        self.func = func  # 处理函数
        self.options = options  # 附带参数
        self.func_type = func_type  # 函数类型


class SYLFK:
    """
    应用程序类
    """
    template_folder = 'templates'

    # 实例化方法
    def __init__(self, static_folder='static'):
        self.host = '127.0.0.1'  # 默认主机
        self.port = 8080  # 默认端口
        self.url_map = {}  # 存放 URL 与 Endpoint 的映射
        self.static_map = {}  # 存放 URL 与静态资源的映射
        self.function_map = {}  # 存放 Endpoint 与请求处理函数的映射
        # 静态资源本地存放路径，默认放在应用所在目录的 static 文件夹下
        self.static_folder = static_folder
        self.route = Route(self)  # 路由装饰器

    # 启动入口
    def run(self, host=None, port=None, **options):
        # 如果有参数且值不为空，则赋值
        for key, value in options.items():
            if value:
                setattr(self, key, value)
        # 如果host和port不为None，则替换
        if host:
            self.host = host
        if port:
            self.port = port

        # 映射静态资源处理函数，所有静态处理函数都是静态资源路由
        self.function_map['static'] = ExecFunc(func=self.dispatch_static,
                                               func_type='static')

        # 加载本地缓存的 session 记录
        session.load_all_session()

        # 把框架本身也就是应用本身和其他几个配置参数传给werkzeug的run_simple方法
        run_simple(hostname=self.host, port=self.port, application=self, **options)

    # 添加路由规则
    @exceptions.capture(ERROR_MAP)
    def add_url_rule(self, url, func, func_type, endpoint='', **kw):

        # 如果节点未命名，使用处理函数的名字
        endpoint = endpoint or func.__name__

        # URL 存在则抛出异常
        if url in self.url_map:
            raise exceptions.URLExistsError

        # 如果类型不是静态资源，且节点已存在，则抛出异常
        if endpoint in self.function_map and func_type != 'static':
            raise exceptions.EndpointExistsError

        # 添加 URL 与节点映射
        self.url_map[url] = endpoint

        # 添加节点与请求处理函数映射
        self.function_map[endpoint] = ExecFunc(func, func_type, **kw)

    # 处理静态资源相关请求，返回响应对象
    @exceptions.capture(ERROR_MAP)
    def dispatch_static(self, static_path):
        # 如果静态文件路径不存在，返回异常
        if not os.path.exists(static_path):
            raise exceptions.PageNotFoundError

        key = parse_static_key(static_path)  # 文件代号
        file_type = TYPE_MAP.get(key, 'text/plain')  # 文件类型

        with open(static_path, 'rb') as f:
            data = f.read()
        return Response(data, content_type=file_type)

    # 处理请求，返回响应对象
    @exceptions.capture(ERROR_MAP)
    def dispatch_request(self, request, status=200):
        # 定义响应报头， Server 字段的值表示运行的服务名
        # 通常由 IIS, Apache, Tomcat, Nginx 等
        # 这里自定义为 Haha Web 0.1
        headers = {'Server': 'Haha Web 0.1'}

        # 从 URL 中提取路径
        url = request.base_url.replace(request.host_url, '/')

        # 从请求中取出 Cookie
        cookies = request.cookies
        if 'session_id' not in cookies:
            headers['Set-Cookie'] = 'session_id={}'.format(create_session_id())

        # 如果路径以静态资源目录开头，则请求的是静态资源，节点为 'static'
        if url.startswith('/' + self.static_folder + '/'):
            endpoint = 'static'
            url = url[1:]
        else:
            # 从映射表中获取节点
            endpoint = self.url_map.get(url, None)

        # 如果节点为空，返回异常
        if endpoint is None:
            raise exceptions.PageNotFoundError

        # 获取节点对应的执行函数
        exec_function = self.function_map[endpoint]

        # 判断执行函数类型作进一步处理
        if exec_function.func_type == 'route':
            # 判断请求方法是否支持
            if request.method in exec_function.options.get('methods'):
                # 判断视图函数的执行是否需要请求对象 request 参与
                # argcount 的值是视图函数的位置参数 + 默认参数的数量之和
                argcount = exec_function.func.__code__.co_argcount
                if argcount > 0:
                    # 需要附带请求体进行结果处理
                    rep = exec_function.func(request)
                else:
                    rep = exec_function.func()
            else:
                # 抛出请求方法不支持异常
                raise exceptions.InvalidRequestMethodError

        elif exec_function.func_type == 'view':
            # 所有视图函数都需要附带请求头获取处理结果
            rep = exec_function.func(request)

        elif exec_function.func_type == 'static':
            # 静态资源返回的是一个预先封装好的响应体，直接返回
            return exec_function.func(url)
        else:
            # 返回 503 错误
            raise exceptions.UnknownFuncError

        # 定义响应体类型
        content_type = 'text/html; charset=UTF-8'

        if isinstance(rep, Response):
            return rep

        # 返回响应体
        return Response(rep, content_type=content_type, headers=headers,
                        status=status)

    # 添加视图规则
    def bind_view(self, url, view_class, endpoint):
        """
        添加视图函数
        :param url: URL 中的路径
        :param view_class: 视图类
        :param endpoint: 节点（控制器名 + 视图函数名）
        """
        # 调用视图类的 get_func 类方法创建一个视图函数并返回
        # 调用此函数即为调用视图类的实例的 dispatch_request 方法
        # 它会调用视图类的实例 GET/POST 方法并返回
        func = view_class.get_func(endpoint)
        self.add_url_rule(url, func=func, func_type="view")

    # 控制器加载
    def load_controller(self, controller):
        # 遍历控制器的 url_map 成员
        for rule in controller.url_map:
            # 绑定 URL 与视图对象
            # 最后的节点名格式为 控制器名 + “.” + 节点名
            self.bind_view(rule['url'], rule['view'],
                           controller.name + "." + rule['endpoint'])

    # 框架被 WSGI 调用入口的方法
    def __call__(self, environ, start_response):
        return wsgi_app(self, environ, start_response)


def simple_template(path, **options):
    """
    模板引擎接口
    :param path: 模板文件相对于模板目录 templates 的路径
    :param options: 视图函数提供的传入模板文件的键值对
    """

    return replace_template(SYLFK, path, **options)


def redirect(url, status_code=302):
    """
    路由重定向
    """

    # 定义一个响应体
    response = Response('', status=status_code)
    # 为响应体的报头中的 Location 参与与 URL 进行绑定，通知客户端跳转
    response.headers['Location'] = url
    # 返回响应体
    return response


def render_json(data):
    """
    将响应体包装成响应对象并返回
    """

    # 默认响应体类型
    content_type = "text/plain"

    # 如果参数是 dict 或者 list 类型，则转换为 JSON 格式数据
    if isinstance(data, (list, dict)):
        data = json.dumps(data)
        content_type = "application/json"  # json 响应类型，HTTP 的content_type属性定义客户端如何渲染数据

    content_type = '{}; charset=UTF-8'.format(content_type)

    # 返回封装完的响应体
    return Response(data, content_type=content_type, status=200)


@exceptions.capture(ERROR_MAP)
def render_file(file_path, file_name=None):
    """
    根据文件路径创建响应对象，浏览器收到响应对象后显示下载文件弹窗
    :param file_path: 文件路径包含文件名
    :param file_name: 文件名
    """

    # 判断服务器是否有该文件，没有则返回 404 错误
    if not os.path.exists(file_path):
        raise exceptions.FileNotExistsError

    # 判断是否有读取权限，没有则抛出权限不足异常
    if not os.access(file_path, os.R_OK):
        raise exceptions.RequireReadPermissionError

    with open(file_path, 'rb') as f:
        content = f.read()

    # 如果没有设置文件名，则以路径最后一项为文件名
    filename = file_name or file_path.split('/')[-1]

    # 封装响应报头，指定为附件类型 attachment, 并定义下载文件名
    headers = {
        'Content-Disposition': 'attachment; filename={}'.format(filename)
    }

    return Response(content, headers=headers, status=200)

