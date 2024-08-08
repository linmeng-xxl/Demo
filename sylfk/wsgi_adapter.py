# WSGI 入口模块
from werkzeug.wrappers import Request


def wsgi_app(app, environ, start_responser):
    """
    处理请求的核心方法，每次服务器收到请求都会运行这个方法，
    其他代码都是由这个方法内部调用。
    :param app: 应用程序
    :param environ: Werkzeug 提供的请求信息字典对象
    :param start_responser: Werkzeug 提供的进一步处理的函数
    """

    request = Request(environ)
    response = app.dispatch_request(request)

    # 调用响应对象的 __call__ 方法并返回
    # 此方法定义在 werkzeug.wrappers.base_response.BaseResponse 类中
    # 其作用是将响应对象返回给 Werkzeug 这个中间桥梁并由后者转发给客户端
    return response(environ, start_responser)


