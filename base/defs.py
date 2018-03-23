# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-10-22

@author: Robin
'''

class ApiException(BaseException):
    pass

def raiseApiEx(e, c=-1):
    raise ApiException({"code":c, "msg":e})

def apiEx(e, c=-1):
    return ApiException({"code":c, "msg":e})

class PageException(BaseException):
    goto = None
    stopback = True
    def __init__(self, msg=None, goto=None, stopback=True):
        self.goto = goto
        self.stopback = stopback
        BaseException.__init__(self, msg)

def raisePageEx(e):
    raise PageException(e)

class CheckException(BaseException):
    pass

class UserException(BaseException):
    pass

class StopException(BaseException):
    pass

class MessageChannel:
    MSG = 0x01  # 站内消息
    SMS = 0x02  # 短信
    PUSH = 0x04  # 推送
    WX = 0x08  # 微信
    WXA = 0x10  # 小程序模板消息
    ALL = 0xFF  # 全部
    
    NORMAL = MSG | PUSH | WX
    WARN = NORMAL | SMS | WX
    

class Values(object):
    score = 0
    money = 0
    credit = 0
    def __init__(self, arr=[]):
        self.score = self.money = self.credit = 0
        if len(arr) > 0:
            self.score = float(arr[0])
        if len(arr) > 1:
            self.money = float(arr[1])
        if len(arr) > 2:
            self.credit = float(arr[2])
    
    def __bool__(self):
        return self.score != 0 or self.money != 0 or self.credit != 0

    def __nonzero__(self):
        return self.__bool__()

    @property
    def text(self):
        from base.templatetags.irfilters import signfloat
        vs = []
        if self.score != 0:
            vs.append(u'积分%s' % (signfloat(self.score)))
        if self.money != 0:
            vs.append(u'余额%s' % (signfloat(self.money)))
        if self.credit != 0:
            vs.append(u'信用额度%s' % (signfloat(self.credit)))
        return u','.join(vs)


class NoValue(object):
    def __bool__(self):
        return False

    def __nonzero__(self):
        return False


class ApiParam(object):
    name = ''
    default = NoValue
    type = None
    empty = False
    examples = None
    choices = None
    remark = None
    testvalue = None

    @property
    def defaultval(self):
        v = self.default if self.default != NoValue else ((self.choices[0][0] if self.choices else None))
        return v or ''

    @property
    def hasdefault(self):
        return self.default != NoValue

    def __init__(self, name='', **kwargs):
        self.name = name
        for k, v in kwargs.items():
            setattr(self, k, v)
        if 'type' not in kwargs and 'default' in kwargs and self.default != None:
            self.type = type(self.default)
        if not self.examples:
            self.examples = self.defaultval
        self.typename = str(self.type.__name__) if self.type else ''

    def __bool__(self):
        return False

    def __nonzero__(self):
        return False

if __name__ == '__main__':
    v = Values()
    if v:
        print 't'
    



