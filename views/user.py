# coding:utf-8
import time
import datetime
import pdfkit
from flask import request, make_response, render_template, redirect, current_app, session, flash
from ext import falseReturn, trueReturn
from utils.auth import login_requires
from utils.upload import src_url

class user_action():
    def __init__(self, request):
        self.request = request
        self.options =  {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': "UTF-8",
            'footer-center': '[page]',
            'footer-font-size': 8,
            'quiet': '',
            'custom-header': [
                ('Accept-Encoding', 'gzip')
            ],
            'no-outline': None
        }

    def login(self):
        """判断用户名密码是否正确然后登录"""
        from app import db
        from models.model import User
        if self.request.method == 'POST':
            username = self.request.form.get('username')
            passwd = self.request.form.get('password')
            # database
            try:
                user = db.session.query(User).filter_by(nickname=username).all()
            except Exception as e:
                db.session.rollback()
                current_app.logger.debug('user_action login() {}'.format(e))

            if user is not None and len(user)>0 and user[0].passwd == passwd:
                session['userid'] = user[0].id
                return redirect('/')
            else:
                flash('用户名或密码错误')
        return make_response(render_template('login.html')) # GET

    @login_requires
    def history(self):
        """生成历史记录"""
        from app import db
        from models.model import Task, User
        from sqlalchemy.sql import text
        result = []
        tips = ''
        length = 10
        page = int(self.request.args.get('page', '1'))
        
        userid = session.get('userid')
        st = (page - 1) * length # number of item in one page, current return item at [st, st+length]
        u = User.query.get(userid)
        now = datetime.datetime.now()
        start_time = now.strftime('%Y-%m-%d')
        end_time = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        start = self.request.args.get('start', start_time)
        end = self.request.args.get('end', end_time)
        d1 = datetime.datetime.strptime(start, '%Y-%m-%d')
        d2 = datetime.datetime.strptime(end, '%Y-%m-%d')
        interval = (d2 - d1).days
        # invalid duration
        if interval > 3 or interval < 0:
            resp = make_response(
                render_template('history.html', user=u, current=1,
                tips='时间间隔不能超过3天', total=0, limit=length,
                start=start, end=end, history=result, v=time.time())
            )
            return resp
        # query database get task info
        conn = db.engine.connect()
        sqlstr = '''
            select SQL_CALC_FOUND_ROWS * from task where userid = :userid and createAt between :start and :end order by createAt desc limit :st,:lg
            '''
        # query result
        dataList = conn.execute(text(sqlstr), userid=userid, start=start, end=end, st=st, lg=length)
        count = conn.execute('select found_rows()')
        for c in count:
            count = c[0]
        groupid_set = {} # record batch average score
        batchhis = [] # batch history
        for d in dataList:
            srcimage = src_url(d.filekey)
            temp = {
                'taskid': d.taskid,
                'filename': d.filename.split('/')[-1],
                'status': d.status,
                'score': round(float(d.score), 3) * 100, # to be xx.x%
                'result_image': srcimage,
                'image': srcimage,
                'createAt': d.createAt.strftime('%Y-%m-%d %H:%M:%S'),
                'groupid': d.groupid
            }
            result.append(temp)
        resp = make_response(
            render_template('history.html', user=u, current=page, tips=tips,
                total=count, limit=length, start=start, end=end, isbatch=0,
                history=result, batchhis=[],batchcount=0, v=time.time()
            )
        )
        return resp


    @login_requires
    def history_batch(self):
        """批次历史记录"""
        from app import db
        from models.model import Task, User
        from sqlalchemy.sql import text
        result = []
        tips = ''
        length = 10
        page = int(self.request.args.get('page', '1'))
        
        userid = session.get('userid')
        st = (page - 1) * length # number of item in one page, current return item at [st, st+length]中
        u = User.query.get(userid)
        now = datetime.datetime.now()
        start_time = now.strftime('%Y-%m-%d')
        end_time = (now + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        start = self.request.args.get('start', start_time)
        end = self.request.args.get('end', end_time)
        d1 = datetime.datetime.strptime(start, '%Y-%m-%d')
        d2 = datetime.datetime.strptime(end, '%Y-%m-%d')
        interval = (d2 - d1).days
        # invalid duration
        if interval > 3 or interval < 0:
            resp = make_response(
                render_template('history.html', user=u, current=1,
                tips='时间间隔不能超过3天', total=0, limit=length,
                start=start, end=end, history=result, v=time.time())
            )
            return resp
        # query database get task info
        conn = db.engine.connect()
        sqlstr = '''
            select SQL_CALC_FOUND_ROWS * from task where userid = :userid and createAt between :start and :end order by createAt desc
            '''
        # query result
        dataList = conn.execute(text(sqlstr), userid=userid, start=start, end=end)
        groupid_set = {} # record batch average score
        batchhis = [] # batch history
        for d in dataList:
            # batch result begin
            if d.groupid not in groupid_set:
                foldername = '/'.join(d.filename.split('/')[:-1])
                tmp = {
                    'foldername': foldername if foldername is not '' else '非文件夹上传',
                    'groupid': d.groupid,
                    'createAt': d.createAt,
                    'score': round(float(d.score),3),
                    'batchsize': 1
                }
                batchhis.append(tmp)
                groupid_set[d.groupid] = {'score':float(d.score), 'count':1}
            else:
                groupid_set[d.groupid]['score'] += round(float(d.score),3)
                groupid_set[d.groupid]['count'] += 1
        for d in batchhis:
            d['score'] = round(groupid_set[d['groupid']]['score'] / groupid_set[d['groupid']]['count'], 3) * 100  # to be xx.x%
            d['batchsize'] = groupid_set[d['groupid']]['count']
        batchhis = batchhis[st:st+length] # just return queryed [st:st+lg]
        batchcount = len(groupid_set)
        current_app.logger.debug("batchcount:{} batchhis:{}".format(batchcount, batchhis))
        resp = make_response(
            render_template('history.html', user=u, current=page, tips=tips,
                limit=length, start=start, end=end, batchcount=batchcount,
                batchhis=batchhis, v=time.time(), isbatch=1
            )
        )
        return resp

    @login_requires
    def report(self):
        """生成pdf报告"""
        from app import db
        from models.model import Task, User
        current_app.logger.debug("report")
        type = self.request.args.get('type', '')
        operate = self.request.args.get('operate', 'preview')

        if type == '' : return redirect('/') # invalid download type
        elif type == 'single' : # download single report
            task_id = self.request.args.get('taskid', '')
            if task_id == '': return redirect('/')
            
            task = Task.query.get(task_id)
            current_app.logger.debug("report task:{}".format(task))
            d = [{
                'result_image': src_url(task.filekey),
                'filename': task.filename,
                'score': round(float(task.score) * 100, 1), # to be xx.x%
                'createAt': task.createAt,
            }]
        elif type == 'group': # download same batch
            group_id = self.request.args.get('groupid', '')
            if group_id == '': return redirect('/')
            task_list = Task.query.filter_by(groupid=group_id)
            d = [{
                'result_image': src_url(task.filekey),
                'filename': task.filename,
                'score': round(float(task.score) * 100, 1), # to be xx.x%
                'createAt': task.createAt,
            } for task in task_list]
            d.sort(key=lambda x:x['score'], reverse=True)
        elif type == 'time': # download report in specified time interval
            pass

        if operate == 'preview':
            string = render_template('report.html', d=d, width='100%')
            resp = make_response(string)
            return resp
        else:
            string = render_template('report.html', d=d, width='400px')
            pdf = pdfkit.from_string(string, False, options=self.options)
            result = make_response(pdf)
            from urllib.parse import quote
            if type == 'single':
                filename = '{}人工智能评分报告.pdf'.format(task.filename.rsplit('.', 1)[0])
            else:
                filename = '{}人工智能评分报告.pdf'.format(group_id)
            result.headers["Content-Disposition"] = (
                "attachment; filename='{0}'; filename*=UTF-8''{0}".format(quote(filename)))
            result.headers['Content-Type'] = 'application/pdf'
            return result