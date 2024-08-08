import pymysql
import pymysql.cursors


class DBResult:
    """操作数据库后的返回结果类
    该类的实例为返回结果生成的对象，包括执行成功与否、异常信息、影响行数等信息
    """
    success = False  # 执行成功与否
    result = None  # 执行结果，通常是查询结果集，一个列表嵌套字典的结构
    error_info = None  # 异常信息
    rows = None  # 影响行数

    def index_of(self, index):
        """返回结果集合中指定索引的一条数据
        """
        # 判断是否执行成功、index 是否为整数且在有效范围内
        if self.success and isinstance(index, int) and self.rows > index >= 0:
            return self.result[index]

    def get_first(self):
        """返回结果集中的第一条数据"""
        return self.index_of(0)

    def get_last(self):
        """返回结果集中的最后一条数据"""
        return self.index_of(-1)

    @staticmethod
    def handler(func):
        """捕获操作数据库时触发的异常的装饰器"""
        def decorator(*args, **options):
            ret = DBResult()
            try:
                # 为 DBResult 实例的 rows 和 result 属性赋值
                ret.rows, ret.result = func(*args, **options)
                # 修改执行状态为 True 表示成功
                ret.success = True
            except Exception as e:
                # 如果捕获到异常，将异常放进 DBResult 对象的 error_info 属性
                ret.error_info = e
            # 返回 DBResult 实例
            return ret
        return decorator

    def to_dict(self):
        """返回四个基本属性构成的字典对象"""
        return {
            'success': self.success,
            'result': self.result,
            'error_info': str(self.error_info),
            'rows': self.rows
        }


class BaseDB:
    """数据库客户端类，该类的实力即为连接数据库的对象"""

    def __init__(
            self,
            user,
            password,
            database='',
            host='127.0.0.1',
            port=3306,
            charset='utf8',
            cursor_class=pymysql.cursors.DictCursor
    ):
        self.user = user  # 用户名
        self.password = password  # 密码
        self.database = database  # 数据库
        self.host = host  # 主机名，默认 127.0.0.1
        self.port = port  # 端口号，默认 3306
        self.charset = charset  # 数据库编码，默认 UTF-8
        self.cursor_class = cursor_class  # 数据库游标类型，默认 DictCursor
        self.conn = self.connect()  # 数据库连接对象

    # 建立连接
    def connect(self):
        return pymysql.connect(host=self.host, user=self.user, port=self.port,
                               password=self.password, db=self.database,
                               charset=self.charset, cursorclass=self.cursor_class)

    # 断开连接
    def close(self):
        self.conn.close()

    # 次装饰器利用被装饰的函数的返回值创建一个 DBResult 类的实例并返回
    # execute 方法的返回值是 DBResult 类的实例
    @DBResult.handler
    def execute(self, sql, params=None):
        """执行 SQL 语句并返回 DBResult 类的实例"""
        # 获取数据库连接对象的游标，这是一个上下文对象
        with self.conn.cursor() as cursor:
            # 如果参数是字典类型，将其和 SQL 语句一起传入 execute 方法
            # 反之只使用 SQL 语句调用 execute 方法
            # 执行结果为涉及的数据的行数，将其赋值给变量 rows
            if isinstance(params, dict):
                rows = cursor.execute(sql, params)
            else:
                rows = cursor.execute(sql)
            # 获取执行结果
            result = cursor.fetchall()
            self.conn.commit()
        # 返回影响条目数量和执行结果
        return rows, result

    # 插入数据并获取最新插入的数据标识，也就是主键索引 ID 字段
    def insert(self, sql, params=None):
        # 获取 SQL 语句执行之后的 DBResult 对象
        ret = self.execute(sql, params)
        # 为 DBResult 对象的 result 属性重新赋值为插入数据的 ID
        ret.result = self.conn.insert_id()
        # 返回 DBResult 对象
        return ret

    # 存储过程调用
    @DBResult.handler
    def process(self, func, params=None):
        with self.conn.cursor() as cursor:
            if isinstance(params, dict):
                rows = cursor.callproc(func, params)
            else:
                rows = cursor.callproc(func)
            result = cursor.fetchall()
            self.conn.commit()
        return rows, result

    # 创建数据库
    def create_db(self, db_name, db_charset='utf8'):
        sql = 'CREATE DATABASE {} CHARSET {}'.format(db_name, db_charset)
        return self.execute(sql)

    # 删除数据库
    def drop_db(self, db_name):
        sql = 'DROP DATABASE {}'.format(db_name)
        return self.execute(sql)

    # 选择数据库
    @DBResult.handler
    def choose_db(self, db_name):
        # 调用 PyMySQL 的 select_db 方法选择数据库
        self.conn.select_db(db_name)
        # 没有影响, 返回空值
        return None, None

