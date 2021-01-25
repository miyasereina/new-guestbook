import pymysql
from flask import Flask, request, jsonify, session, render_template
from gevent import pywsgi

app=Flask(__name__)
app.secret_key='123456'


con=pymysql.connect(user='root',password='reina0526', charset='utf8')
cursor=con.cursor()
cursor.execute("create database if not exists test character set utf8;")
cursor.execute("use test")
cursor.execute("create table if not exists"
            " user(username char(20),nickname char(20),password char(20),sex char(1))character set utf8;")
cursor.execute("create table if not exists guestbook"
            "(content_id int primary key auto_increment,content char(200),username char(20),nickname char(20),post_time timestamp(6),last_correct timestamp(6))"
            "character set utf8;")
@app.route('/',methods=['GET'])
def board():
    cursor.execute('select*from guestbook')
    value=cursor.fetchall()
    board=jsonify(value)
    return board

@app.route('/guestbook',methods=['POST'])
def write():
    data=request.get_json(force=True)
    username=session.get('username')
    if username is None:
        raise HttpError(401, '请先登录')
    content=data.get('content')
    cursor.execute('select nickname from guestbook where username=%s',(username))
    nickname=cursor.fetchone()
    cursor.execute('insert into `guestbook`(`content`,`username`,`post_time`,`nickname`) values(%s,%s,now(),%s)',
                   (content,username,nickname))
    con.commit()
    return "发表成功"

@app.route('/guestbook/content',methods=["PUT"])
def correct():
    data=request.get_json(force=True)
    username=session.get('username')
    content_id=data.get('content_id')
    content=data.get('content')
    if username is None:
        raise HttpError(401, '请先登录')
    cursor.execute('update `guestbook` set `content`=%s,last_correct=now() where username=%s and content_id=%s',
                   (content,username,content_id))
    con.commit()
    return '修改成功'

@app.route('/guestbook/deletion',methods=['DELETE'])
def deletion():
    data=request.get_json(force=True)
    content_id=data.get('content')
    username=session.get('username')
    if username is None:
        raise HttpError(401, '请先登录')
    cursor.execute('delete from`guestbook` where username=%s and content=%s',(username,content_id))
    con.commit()
    return '删除成功'

@app.route('/user', methods=['POST','GET'])
def register():
    data=request.get_json(force=True)
    username=data.get('username')
    nickname=data.get('nickname')
    password=data.get('password')
    sex=data.get("sex")
    cursor.execute('select count(*) from `user` where `username`=%s',(username,))
    count=cursor.fetchone()
    if count[0]>=1:
        raise HttpError(400, '用户名已存在')
    if username is None:
        raise  HttpError(400,"请输入username")
    if nickname is None:
        raise HttpError(400, "请输入nickname")
    if password is None:
        raise HttpError(400, "请输入password")
    if sex is None:
        raise HttpError(400, "请输入sex")
    cursor.execute('insert into `user`(`username`,`nickname`,`password`,`sex`) values (%s, %s,%s,%s)',(username, nickname, password, sex))
    con.commit()
    return "注册成功"

@app.route('/me',methods=['GET'])
def my_information():
    username=session.get('username')
    if username is None:
        raise HttpError(401, "请先登录")
    cursor.execute('select `username`, `nickname`,`sex` from `user` where `username`=%s', (username,))
    data=cursor.fetchall()
    response=jsonify(data)
    return response




@app.route('/login', methods=['POST'])
def login():
    data=request.get_json(force=True)
    username=data.get('username')
    password=data.get('password')
    cursor.execute('select `username`, `password` from `user` where `username`=%s', (username,))
    values=cursor.fetchone()
    if values is None:
        raise HttpError(402, '用户名或密码错误')
    if username!=values[0] or password!=values[1]:
        raise HttpError(402, '用户名或密码错误')
    session['username']=username
    session['password']=password
    return '登录成功'


@app.route('/users/username', methods=['PUT'])
def change_username():
    data=request.get_json(force=True)
    username=session.get('username')
    if username is None:
        raise HttpError(401, '请先登录')
    username2=data.get('username2')
    cursor.execute('select count(*) from `user` where `username`=%s', (username2,))
    count=cursor.fetchone()[0]
    if count>=1:
        raise HttpError(400, '用户名已存在')
    cursor.execute('update `user` set `username`=%s where username=%s', (username2, username))
    con.commit()
    session['username']=username2
    return '修改用户名成功'


@app.route('/users/password', methods=['PUT'])
def change_password():
    data=request.get_json(force=True)
    username=session['username']
    password=data.get('password')
    if username is None:
        raise HttpError(401, '请先登录')
    cursor.execute('update `user` set `password`=%s where username=%s',(password,username))
    con.commit()
    session['password']=password
    return '修改密码成功'

class HttpError(Exception):
    def __init__(self, status_code, message):
        super().__init__()
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {
            'status': self.status_code,
            'msg': self.message
        }
@app.errorhandler(HttpError)
def handle_http_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

if __name__ == '__main__':
    server=pywsgi.WSGIServer(('0.0.0.0',8000),app)
    server.serve_forever()
