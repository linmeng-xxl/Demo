from sylfk.view import Controller

from core.base_view import BaseView, SessionView

from sylfk import SYLFK, simple_template

from sylfk.session import session

from sylfk import redirect, render_json, render_file

from core.database import dbconn

from sylfk import exceptions, ERROR_MAP, content_type


# 首页视图
class Index(SessionView):
    def get(self, request, *args, **options):
        # 获取当前会话中的 user 的值
        user = session.get_item(request, 'user')
        # 把 user 的值用模板引擎置换到页面中并返回
        return simple_template("index.html", user=user, message="实验楼，你好")


# 登录视图
class Login(BaseView):
    def get(self, request, *args, **options):
        # 从 GET 请求中获取 state 参数，如果不存在则返回默认值 1
        state = request.args.get('state', "1")
        # 当 state 不为 1 时，返回用户不存在
        message = "输入登录用户名" if state == '1' else "用户名不存在"
        return simple_template("layout.html", title="登录", message=message)

    def post(self, request, *args, **options):
        # 把用户提交的信息到数据库中进行查询
        sql = "SELECT * FROM user WHERE user.f_name = '{}'".format(request.form['user'])
        ret = dbconn.execute(sql)
        # 如果有匹配结果，说明注册过，反之再次重定向登录页面
        if ret.rows == 1:
            # 获取第一条数据的 f_name 字段为用户名
            user = ret.get_first()['f_name']
            # 把 user 存放到当前会话中
            session.push(request, 'user', user)
            # 返回登录成功提示和首页链接
            return redirect("/")
        # 设置 state=0 表示注册过
        return redirect("/login?state=0")


# 登出视图
class Logout(SessionView):
    def get(self, request, *arges, **options):
        # 从当前会话中删除 user
        session.pop(request, 'user')
        # 返回登出成功提升和首页链接
        return redirect("/")


class API(BaseView):
    def get(self, request, *args, **options):
        data = {
            'name': 'shiyanlou_001',
            'company': '实验楼',
            'department': '课程部'
        }
        return render_json(data)


class Download(BaseView):
    def get(self, request, *args, **options):
        return render_file("main.py")


class Register(BaseView):
    def get(self, request, *args, **options):
        # 收到 GET 请求是通过模板返回一个注册页面
        return simple_template("layout.html", title="注册", message="输入注册用户名")

    def post(self, request, *args, **options):
        # 把用户提交的信息作为参数
        # 执行 SQL 的 INSERT 语句把信息保存到数据库的表中
        sql = "INSERT INTO user(user.f_name) VALUE('{}')".format(request.form['user'])
        ret = dbconn.insert(sql)
        # 如果添加成功，则表示注册成功，重定向到登录页面
        if ret.success:
            return redirect("/login")
        else:
            # 添加失败返回 错误信息
            return render_json(ret.to_dict())


@exceptions.reload(404, ERROR_MAP)
def test_reload():
    return '<h1>测试重载 404 异常</h1>', content_type, 404


syl_url_map = [
    {
        'url': '/',
        'view': Index,
        'endpoint': 'index'
    },
    {
        'url': '/login',
        'view': Login,
        'endpoint': 'login'
    },
    {
        'url': '/logout',
        'view': Logout,
        'endpoint': 'logout'
    },
    {
        'url': '/api',
        'view': API,
        'endpoint': 'api'
    },
    {
        'url': '/download',
        'view': Download,
        'endpoint': 'download'
    },
    {
        'url': '/register',
        'view': Register,
        'endpoint': 'register'
    }
]

app = SYLFK()

index_controller = Controller('index', syl_url_map)
app.load_controller(index_controller)

app.run(use_reloader=True)
