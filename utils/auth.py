# coding:utf-8
from flask import session, redirect
from functools import wraps

def login_requires(f):
    @wraps(f)
    def control_decorated_function(*args, **kwargs):
        try:
            s = session.get('userid', '')
            if s == '': return redirect('/')
        except:
            return redirect('/')
        return f(*args, **kwargs)
    return control_decorated_function