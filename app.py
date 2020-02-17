# coding:utf-8
import os
import time
import logging

from flask import Flask, send_from_directory, render_template, make_response, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from kombu import Queue
from celery import Celery
import celery.result as cr

from views.score import score_action
from views.user import user_action
from models.model import *
from utils.upload import src_url

import config
import celeryconfig

app=Flask(__name__, static_folder='./static', template_folder='./templates')
app.config.from_object(config)
db = SQLAlchemy(app)

classify_app = Celery()
if config.USE_GPU:
    classify_app.config_from_object(celeryconfig.ClassifyGPUConfig)
else:
    classify_app.config_from_object(celeryconfig.ClassifyCPUConfig)
classify_app.conf.task_queues = (
    Queue('chromo-task', routing_key='chromo-task'),
)

res_app = Celery()
res_app.config_from_object(celeryconfig.ResultConfig)
res_app.conf.task_queues = (
    Queue('chromo-result', routing_task='chromo-result'),
)

#classify_app.send_task('gpu_worker.classify', args=['filekey'], queue='chromo-task', routing_key='chromo-task')
#res_app.send_task('chromo-result.result_save', args=['xxxx'], queue='chromo-result', routing_key='chromo-result')

@app.route('/static/<path:filename>')
def send_file(filename):
    return send_from_directory(app.static_folder, filename)

# 上传文件夹
@app.route('/upload_folder', methods=['post'])
def send_folder():
    return score_action(request).upload_f()

# index
@app.route('/', methods=['get'])
def index():
    userid = session.get('userid', '')
    if userid == '':
        return redirect('/login')
    try:
        u = db.session.query(User).get(userid)
    except Exception as e:
        app.logger.error("/ query database error:{}".format(e))
        return redirect('/login')

    resp = make_response(
        render_template('index.html', user=u, v=time.time())
    )
    return resp

# 登录
@app.route('/login', methods=['get', 'post'])
def login():
    return user_action(request).login()

# 退出登录
@app.route('/logout', methods=['get'])
def logout():
    session.clear()
    return redirect('/')

# 上传图片
@app.route('/upload', methods=['post'])
def upload_image():
    return score_action(request).upload()

# 请求结果
@app.route('/query', methods=['get', 'post'])
def query_task():
    n = request.args.get('n', 5)
    show_num = int(n) if n != '' else 5
    return score_action(request).query(show_num=show_num)

@app.errorhandler(404)
def page_not_found(error):
    app.logger.error("ERROR:{}".format(error))
    return redirect('/')


@app.errorhandler(Exception)
def error_handler(error):
    app.logger.error("ERROR:{}".format(error))
    return redirect('/')

# 生成pdf
@app.route('/report', methods=['GET'])
def report():
    return user_action(request).report()
# 历史记录
@app.route('/history')
def history():
    return user_action(request).history()

# 批次历史记录
@app.route('/history_batch')
def history_batch():
    return user_action(request).history_batch()

if __name__ == '__main__':
    if hasattr(config, 'LOG') and os.path.exists(config.LOG):
        handler = logging.FileHandler(config.LOG)
        app.logger.addHandler(handler)
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
