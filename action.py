#coding:utf-8
import uuid
import time
import datetime
from flask import jsonify, redirect, render_template, make_response, session, current_app
from ext import trueReturn, falseReturn
import pdfkit
from celery.result import AsyncResult

from utils.upload import Upload_Ali, src_url

class score_action:
    def __init__(self, request):
        self.request = request

    def upload_f(self):
        """上传文件夹"""
        current_app.logger.debug("upload_f() begin")
        from app import db
        from models.model import Task, User
        try:
            groupid = uuid.uuid4().hex
            files = self.request.files
            temp = files.to_dict(flat=False)
            result = []
            for f in temp['file']:
                if 'image' not in f.content_type:
                    continue

                file_name = f.filename.split('/')[-1]
                filekey = Upload_Ali(f) # upload to aliyun
                taskid = self.classify_task(filekey) # task worker
                # new task and commit
                task = Task(taskid=taskid)
                task.createAt = (datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                task.groupid = groupid
                task.filename = file_name
                task.filekey = filekey
                task.status = '1'
                task.userid = session['userid']
                task.score = '0'
                db.session.add(task)
                db.session.commit()
                res_taskid = self.result_task(taskid)
                result.append(res_taskid)

            return jsonify(trueReturn(result))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("upload_f() ERROR:{}".format(e))
            return jsonify(falseReturn('ERROR'))

    def upload(self):
        """上传文件"""
        current_app.logger.debug("upload() begin")
        from models.model import User, Task
        from app import db
        current_app.logger.debug("upload() import fi")
        try:
            groupid = uuid.uuid4().hex
            files = self.request.files
            temp = files.to_dict(flat=False)
            result = []
            for f in temp['file']:
                if 'image' not in f.content_type:
                    continue
                file_name = f.filename.split('/')[-1]
                # upload to aliyun
                file_key = Upload_Ali(f)
                # task worker
                taskid = self.classify_task(file_key)
                #current_app.logger.debug("upload() get taskid:{}".format(taskid))
                task = Task(taskid=taskid)
                task.groupid = groupid
                task.score = '0'
                task.createAt = (datetime.datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                task.filename = file_name
                task.filekey = file_key
                task.status = '1'
                task.userid = session['userid']
                db.session.add(task)
                db.session.commit()
                # result worker
                res_taskid = self.result_task(taskid)
                result.append(res_taskid)

            current_app.logger.debug("upload() before return")
            return jsonify(trueReturn(result))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("upload() ERROR:{}".format(e))
            return jsonify(falseReturn('ERROR'))

    def query(self, show_num=5):
        """使用result-worker的taskid生成AsyncResult来进行同步，然后请求数据库得到结果"""
        from app import db, res_app
        from models.model import Task, User
        result, returnObj = [], {}
        try:
            taskids = self.request.json['taskids'] # result-worker taskid list
            current_app.logger.debug("query() get result worker taskid:{}".format(taskids))
            taskids = [AsyncResult(id=taskid, app=res_app).get() for taskid in taskids]
            #current_app.logger.debug("query() get classify worker taskid:{}".format(taskids))
            if len(taskids) == 0:
                return jsonify(trueReturn(result))
            res_list = [db.session.query(Task).get(taskid) for taskid in taskids]

            #current_app.logger.debug("query() res_list:{} time:{}".format(res_list, time.time()))
            res_list.sort(key=lambda s:s.score)
            for res in res_list[-1:-1-show_num:-1]:
                current_app.logger.debug("query() classify worker taskid:{} score:{}".format(res.taskid, res.score))
                tmp = {
                    'taskid': res.taskid,
                    'groupid': res.groupid,
                    'filename': res.filename,
                    'status': res.status,
                    'score': res.score,
                    'memo': '',
                    'result_image': src_url(res.filekey),
                    'image': '',
                    'createAt': res.createAt,
                    'doneAt': res.doneAt
                }
                result.append(tmp)

            returnObj['data'] = result
            return jsonify(trueReturn(returnObj))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error("query() ERROR:{}".format(e))
            return jsonify(falseReturn('ERROR'))

    def classify_task(self, filekey):
        """启动worker执行任务，并返回taskid"""
        from app import classify_app, res_app
        classify_task = classify_app.send_task('classify_worker.classify', args=[filekey])
        current_app.logger.debug("classify_task() get:{} id:{}".format(filekey, classify_task.id))
        current_app.logger.debug("classify_task() status:{}".format(classify_task.status))
        return classify_task.id

    def result_task(self, taskid):
        """请求结果保存到数据库中"""
        from app import res_app
        res_task = res_app.send_task('result-worker.result_save', args=[taskid])
        current_app.logger.debug("result_task() send")
        return res_task.id