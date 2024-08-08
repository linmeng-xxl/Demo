import sys
import os
from sylfk.dbconnector import BaseDB


db_user = 'root'
db_password = "123456".encode("utf8")
# db_password = os.environ.get('MYSQL_PWD') or '123456'  # 密码
db_database = 'shiyanlou'

try:
    dbconn = BaseDB(db_user, db_password, db_database)
except Exception as e:
    code, _ = e.args

    # 如果异常代码为 1049 就是数据库不存在异常，则创建数据库
    # 否则为未知错误，输出信息并退出
    if code != 1049:
        print(e)
        exit()

    # 获取一个没有数据库的连接对象
    dbconn = BaseDB(db_user, db_password)
    # 创建数据库，返回一个 DBResult 对象
    ret = dbconn.create_db(db_database)

    # 定义创建数据表的语句
    create_table = '''
        CREATE TABLE user (
            id INT PRIMARY KEY  AUTO_INCREMENT,
            f_name VARCHAR(50) UNIQUE 
            )'''

    # 如果创建成功，切换到数据库中
    if ret.success:
        ret = dbconn.choose_db(db_database)
        # 如果切换成功，创建数据表
        if ret.success:
            ret = dbconn.execute(create_table)

    # 如果以上有一步出错，则删除数据库回退
    if not ret.success:
        dbconn.drop_db(db_database)
        print(ret.error_info)
        exit()
