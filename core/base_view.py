from sylfk.view import View

from sylfk.session import AuthSession, session

from sylfk import redirect


class BaseView(View):
    # 定义支持的请求方法，默认支持 GET 和 POST 方法
    methods = ['GET', 'POST']

     # POST 请求处理函数
    def post(self, request, *args, **options):
        pass

    # GET 请求处理函数
    def get(self, request, *arges, **options):
        pass

    # 视图处理函数入口
    def dispatch_request(self, request, *args, **options):
        """
        处理请求的核心函数，该函数会被视图函数调用
        """
        if request.method in self.methods:
            # request.method.lower() 返回请求方法的小写字符串
            func = getattr(self, request.method.lower())
            return func(request, *args, **options)
        return '<h1>Unknown or unsupported require method.</h1>'


class AuthLogin(AuthSession):
    """登录验证类"""

    @staticmethod
    def auth_logic(request, *args, **options):
        """验证逻辑"""
        if 'user' in session.get(request):
            return True
        return False

    @staticmethod
    def auth_fail_callback(request, *args, **options):
        """如果没有通过验证，则返回一个链接点击回到登录页面"""
        return redirect("/login")


class SessionView(BaseView):
    """会话视图基类"""

    # 验证类装饰器
    @AuthLogin.auth_session
    def dispatch_request(self, request, *args, **options):
        # 结合装饰器内部逻辑，调用继承的子类的 dispatch_request 方法
        return super(SessionView, self).dispatch_request(request, *args, **options)
