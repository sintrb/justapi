# -*- coding: UTF-8 -*
'''
Copyright 2015 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2015-8-17

@author: Robin
'''
from django import template
register = template.Library()
DATADIC_CACHE_TIME = 60# * 60
from base.defs import CheckException
from base.utils import get_or_set_cache

@register.filter
def autobr(v):
    if v:
        return v.strip().replace('\n', '<br/>')
    return v
        
@register.filter
def boolsel(v, tv, fv):
    return tv if v else fv

@register.filter
def noquot(v):
    return v.replace('"', '').replace("'", '')


def hasOperation(ops, o):
    from base.siteinfo import get_site
    site = get_site()
    if ops == None:
        return not (isinstance(o, basestring) and o.lower().endswith('_xarea'))
    else:
        if type(o) != list:
            o = o.lower().split('__or__')
        ar = []
        for i in o:
            ar += i.lower().split('__or__')
        for i in ar:
            il = i.lower()
            if il in ops or il not in site.alloperations:
                return True
        return ar

@register.filter(name='hasOperation')
def __hasOperationFilter(ops, o):
    return hasOperation(ops, o) == True

@register.tag
def checkOperation(parser, token):
    bits = token.contents.split()
    oplist = [parser.compile_filter(x) for x in bits[1:]]      
    return CheckOperationTag(oplist)

class CheckOperationTag(template.Node):
    def __init__(self, oplist):
        self.oplist = oplist
    def render(self, context):
        ops = [op.resolve(context) for op in self.oplist]
        meopts = context['me'].operations if context['me'] else []
        ar = hasOperation(meopts, ops)
        if ar != True:
            from base.siteinfo import get_site
            mp = get_site().operationsmap
            raise CheckException(u'需要"%s"权限' % (','.join([mp[k] for k in ar if k in mp])))
        return '<!-- %s -->' % (','.join(ops))


@register.filter
def space2nbsp(v):
    return str(v).replace(' ', '&nbsp;') if v else ''

@register.filter
def autotelhone(s):
    from django.utils.safestring import  SafeText
    import re
    if s:
        for t in re.findall('([0-9\-]{5,100})', s):
            tag = '<a v-tel="%s" href="tel:%s" class="telphone">%s</a>' % (t, t, t)
            s = s.replace(t, tag)
    else:
        s = ''
    return SafeText(s)

def getIds(ids):
    from base.utils import splitstrip
    return ids if type(ids) == list else filter(lambda x:x.isdigit(), splitstrip(str(ids), ','))

@register.filter
def getdatadics(stype, ids=None):
    from preset.models import DataDic
    if stype and (type(stype) == int or stype.isdigit() or ',' in stype):
        ids = stype
        stype = None
    ids = getIds(ids)
    if not stype and not ids:
        return []
    query = DataDic.objects.filter()
    if stype:
        query = query.filter(type=stype)
    if ids:
        query = query.filter(id__in=ids)
        dd = {
         d.id:d
         for d in query
         }
        res = [dd[int(i)] for i in ids if dd.get(int(i))]
        query = res
    return query

@register.filter
def getdatadic(did):
    from preset.models import DataDic
    return DataDic.objects.filter(pk=did).first()
    
@register.filter
def getdatadicjson(did):
    return get_or_set_cache(u'datadic_%s' % (did), lambda :getdatadic(did).to_json, DATADIC_CACHE_TIME)

@register.filter
def getdatadicsjson(stype, ids=None):
    ids = getIds(ids)
    key = u'datadics_%s' % ((stype or '') + '-'.join([str(i) for i in ids]),)
    return get_or_set_cache(key, lambda : [v.to_json() for v in getdatadics(stype, ids)], DATADIC_CACHE_TIME)

@register.filter
def getdatadicstext(stype, ids=None):
    return u','.join([v['value'] for v in getdatadicsjson(stype, ids)])

@register.filter
def splittoint(text, seg=','):
    from base.utils import splitstrip
    return [int(s) for s in splitstrip(text, seg) if s.isdigit()]

@register.filter
def getbeforedate(days=None):
    days = int(days)
    from datetime import datetime
    from datetime import timedelta
    return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

@register.filter
def orderitemtoaoi(objid):
    from agency.models import AgencyOrderItem
    aoi = AgencyOrderItem.objects.filter(orderitem_id=objid)
    return aoi

@register.filter
def wraptophones(text):
    import re
    if not text:
        return ''
    rs = re.findall("([^\d]*)(\d+)", text)
    if not rs:
        return text
    ls = []
    for g in rs:
        ls.append('<span style="display:inline-block">%s<a href="tel:%s" class="btn btn_call" onclick="event.stopPropagation();">拨打电话</a></span>' % (u''.join([c for c in g[0] if c not in u'><，,; ']), g[1]))
    return u' '.join(ls)

@register.filter
def linkwrap(s):
    from django.utils.safestring import SafeText
    import re
    if s:
        for tx, sid in re.findall('(S\d{8}0+(\d+))', s):
            tag = '<a href="/order/{sid}" style="color: #FE6904;">{tx}</a>'.format(sid=sid, tx=tx)
            s = s.replace(tx, tag)
#         for tx, bid in re.findall('(B\d{8}0+(\d+))', s):
#             tag = '<a href="/me/bigorder/{bid}" style="color: #FE6904;">{tx}</a>'.format(bid=bid, tx=tx)
#             s = s.replace(tx, tag)
    else:
        s = ''
    return SafeText(s)

@register.filter
def logicor(a,b):
    return a or b


@register.filter
def template_args(instance, arg):
    '''将参数添加到实例的一个属性里'''  # 由于是侵入型，单实例会有问题
    if not hasattr(instance, "_TemplateArgs"):
        setattr(instance, "_TemplateArgs", [])
    instance._TemplateArgs.append(arg)
    return instance

@register.filter
def template_method(instance, method):
    '''执行实例的方法'''
    method = getattr(instance, method)
    if hasattr(instance, "_TemplateArgs"):
        if 'notarg' in instance._TemplateArgs:
            to_return = method()
        else:
            to_return = method(*instance._TemplateArgs)
        delattr(instance, '_TemplateArgs')
        return to_return
    return method()

@register.filter
def getobjnamebyobjid(did, modelname):
    from xadmin.views import AdminView
    m = AdminView().get_model(modelname)
    if m:
        return m.objects.filter(pk=did).first().name or m.objects.filter(pk=did).first() if did else ''
    else:
        return '未找到'

@register.filter
def concat(a,b):
    return u'%s%s'%(a, b)

@register.filter
def newschannelsfilter(query, channels):
    from base.utils import splitstrip
    from django.db.models import Q
    q = Q(channels__isnull=True)
    for c in splitstrip(channels, ','):
        q |= Q(channels__icontains=u'[%s]' % c)
    return query.filter(q)

@register.filter
def begin(name, args=''):
    return {
        'name': name,
        'args': args.split(',')
    }

@register.filter
def call(cxt, obj):
    return getattr(obj, cxt['name'])(*cxt['args'])
