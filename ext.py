# -*- coding:utf-8 -*-

def trueReturn(msg):
    return {
        'status': True,
        'data': msg,
        'message': ''
    }


def falseReturn(msg):
    return {
        'status': False,
        'data': '',
        'message': msg
    }
