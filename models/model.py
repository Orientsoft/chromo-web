# coding: utf-8
from app import db

# class User_(db.Model):
#     __tablename__ = 'user'

#     openid = db.Column(db.String(45), primary_key=True, unique=True)
#     nickname = db.Column(db.String(45), nullable=False)
#     icon_url = db.Column(db.String(300), nullable=False)
#     gender = db.Column(db.String(2), nullable=False)
#     city = db.Column(db.String(45))
#     phone = db.Column(db.String(11))
#     bal = db.Column(db.INTEGER, nullable=False, server_default=db.text("'0'"))
#     update_time = db.Column(db.DateTime, nullable=True)
#     unionid = db.Column(db.String(45))
#     status = db.Column(db.INTEGER)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(45), primary_key=True, unique=True)
    nickname = db.Column(db.String(45))
    icon_url = db.Column(db.String(300), nullable=False)
    passwd = db.Column(db.String(45), nullable=False)

    def __repr__(self):
            return '<User>: id:({}) nickname:({})'.format(self.id, self.nickname)


class Task(db.Model):
    __tablename__ = 'task'
    taskid = db.Column(db.String(45), primary_key=True, unique=True)
    groupid = db.Column(db.String(45)) # 将检查分为批次，groupid为批次的id，可以一次下载整个批次的pdf
    createAt = db.Column(db.DateTime)
    doneAt = db.Column(db.DateTime)
    filename = db.Column(db.String(200))
    filekey = db.Column(db.String(300))
    score = db.Column(db.String(45))
    userid = db.Column(db.String(45), db.ForeignKey('user.id'))
    status = db.Column(db.String(45)) # 表示状态 1表示正在检测 2 表示检测成功 3表示检测失败

    def __repr__(self):
        return '<Task>: taskid:({}) createAt:({}) filename:({}) score:({})'.format(self.taskid, self.createAt, self.filename, self.score)