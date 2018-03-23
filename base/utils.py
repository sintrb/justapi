# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-10-22

@author: Robin
'''
from irlocks import Lock
from datetime import datetime
def get_queryfilters(param, trans=None):
    q = {}
    for k in param:
        if k.startswith("q__"):
            v = param[k]
            if v:
                q[k[3:]] = v if not trans or v not in trans else trans[v]
    return q

def get_pageinfo(param, size=10, page=1):
    size = int(param.get('size', param.get('rows', size)))
    if size < 0:
        size = 100000
    page = 'page' in param and int(param['page']) or page
    start = size * (page - 1)
    return (size, page, start)

def get_subquery_filter(query, subkey, v):
    rs = subkey.split('.')
    fieldname = rs[0]
    filtername = rs[1]
    model = query.model
    field = model.get_field(fieldname)
    rmodel = field.rel.to
    rquery = warp_query(rmodel.objects.filter(), param={filtername:v}).values_list('id')
    rids = [r[0] for r in rquery]
    return '%s_id__in' % fieldname, rids

def warp_query(query, trans={'True':True, 'False':False}, param=None):
    if param:
        qs = get_queryfilters(param, trans)
        from django.db.models import Q
        nqs = {}
        Q()
        for k, v in qs.items():
            if '__or__' in k:
                ks = k.split('__or__')
                nks = {}
                for sk in ks:
                    if '.' in sk:
                        sqk, sqv = get_subquery_filter(query, sk, v)
                        if sqk in nks:
                            nks[sqk] = nks[sqk] + sqv
                        else:
                            nks[sqk] = sqv
                    else:
                        nks[sk] = v
                q = Q()
                for nk, nv in nks.items():
                    q = q | Q(**{nk:nv})
                query = query.filter(q)
            elif k.startswith('not__'):
                q = Q(**{k[5:]:v})
                query = query.exclude(q)
            else:
                if k.endswith('__in'):
                    v = splitstrip(v, ',')
                if '.' in k:
                    sqk, sqv = get_subquery_filter(query, k, v)
                    if sqk in nqs:
                        nqs[sqk] = nqs[sqk] + sqv
                    else:
                        nqs[sqk] = sqv
                else:
                    nqs[k] = v
        if nqs:
            query = query.filter(**nqs)
#     print size, page, start

    if param and param.get('searchtype') and param.get('keyword'):
        st = param.get('searchtype')
        kw = param.get('keyword')
        model = query.model
        if '.' in st:
            rs = st.split('.')
            fieldname = rs[0]
            filtername = rs[1]
            field = model.get_field(fieldname)
            rmodel = field.rel.to
            rquery = warp_query(rmodel.objects.filter(), param={filtername:kw}).values_list('id')
            rids = [r[0] for r in rquery]
            query = query.filter(**{fieldname + '_id__in':rids})
        else:
            query = warp_query(query, param={st:kw})

    if param and 'sort' in param:
        query = query.order_by(u'%s%s' % ('-' if 'order' in param and param['order'] == 'desc' else '', param['sort']))
    if param and 'orderby' in param:
        query = query.order_by(*[v.strip() for v in param['orderby'].split(',') if v.strip()])
    
    return query

def gen_pager(query, trans={'True':True, 'False':False}, size=10, page=1, param=None):
    start = 0
    if param:
        size, page, start = get_pageinfo(param, size, page)
    else:
        size, page = int(size), int(page)
        start = size * (page - 1)
    
    query = warp_query(query, trans, param)
    
    count = query.count()
    rawquery = query
    items = query[start:size * page]
    firstpage = 1
    lastpage = (count - 1) / size + 1
    
    res = {
            'itemsquery':items,
            'rawquery':rawquery,
            'items':items,
            'count':count,
            'page':page,
            'size':size,
            'start':start,
            'prevpage':page - 1 if page > 1 else 1,
            'nextpage':page + 1 if page < lastpage else lastpage,
            'prev':page - 1 if page > 1 else False,
            'next':page + 1 if page < lastpage else False,
            'first':firstpage if page > firstpage else False,
            'last':lastpage if page < lastpage else False,
            'lastpage':lastpage,
            'firstpage':firstpage,
            }
    res['needpager'] = res['next'] or res['prev']
    return res

def gen_pager_array(query, trans=None, size=10, page=1, param=None, func=None):
    res = gen_pager(query, trans, size, page, param)
    items = res['items']
    start = res['start']
    count = res['count']
    size = res['size']
    return Array(items=[o if not func else func(o) for o in items], start=start, total=count, size=size, rawquery=res['rawquery'])
    
def obj2dic(o, ks, d=None):
    if d == None:
        d = {}
    for k in ks:
        d[k] = getattr(o, k)
    return d

def dic2obj(o, ks, d):
    for k in ks:
        if k in d:
#             print '%s:%s'%(k,d[k])
            setattr(o, k, d[k])

def dic2objRefs(o, fs, d):
    for f in fs:
        fk = '%s_id' % f
        if fk not in d:
            continue
        if not d.get(fk) or str(d.get(fk)) == '0':
            setattr(o, f, None)
        else:
            setattr(o, fk, d.get(fk))

def obj2obj(dst, ks, src):
    for k in ks:
        if hasattr(src, k):
            setattr(dst, k, getattr(src, k))

def dic2objNums(o, fs, d):
    for fk in fs:
        if fk not in d:
            continue
        if not d.get(fk):
            setattr(o, fk, 0)
        else:
            setattr(o, fk, d.get(fk))

def dic2objDateTimes(o, fs, d):
    for fk in fs:
        if fk not in d:
            continue
        if not d.get(fk):
            setattr(o, fk, None)
        else:
            setattr(o, fk, parse_datetime(d.get(fk)) or parsedate(d.get(fk)))

class Data(object):
    def __init__(self, data=None):
        self.data = data

class Array(Data):
    @property
    def data(self):
        return {
                "items":self.items, "start":self.start, "total":self.total
                }
    def __init__(self, items, start=0, total=-1, rawquery=None, size=-1):
        self.items = items
        self.start = start
        self.size = size or len(items)
        self.total = total if total != -1 else len(items)
        self.rawquery = rawquery

def json_filed_default(obj):
    import decimal
    import datetime
    import time
    from django.db.models.fields.files import ImageFieldFile
    from django.db.models.query import QuerySet
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    if isinstance(obj, datetime.datetime):
        return obj.timetuple()
    if isinstance(obj, datetime.date):
        return obj.timetuple()
    if isinstance(obj, datetime.time):
        return obj.strftime('%H:%M:%S')
    if isinstance(obj, time.struct_time):
        return {"timestamp":time.mktime(obj), "date":time.strftime('%Y-%m-%d', obj)}
    if isinstance(obj, ImageFieldFile):
        if hasattr(obj, 'url'):
            return obj.url
        else:
            return ''
    if isinstance(obj, QuerySet):
        return [o for o in obj]
    if hasattr(obj, 'to_json'):
        to_json = obj.to_json
        return to_json() if callable(to_json) else to_json
            
    raise TypeError(type(obj))

def get_one_by_sql(sql, params=None, db=None):
    from django.db import connection
    cursor = connection[db].cursor() if db else connection.cursor()
    cursor.execute(sql, params)
    r = cursor.fetchone()
    cursor.close()
    return r

def objstrip(obj):
    if type(obj) == dict:
        keys = obj.keys()
        for k in keys:
            if not obj[k]:
                del obj[k]
            else:
                objstrip(obj[k])
    elif type(obj) == list or type(obj) == tuple:
        for o in obj:
            objstrip(o)
    return obj

def splitstrip(strs, seg=' '):
    if not strs:
        return []
    return [s.strip() for s in strs.split(seg) if s.strip()]


def orderinggen():
    import time
    return max(int(time.time()), 0)

class Ix(object):
    _index = -1

    @property
    def start(self):
        self._index = 0
        return self._index

    @property
    def next(self):
        self._index += 1
        return self._index

    def span(self, v):
        v -= 1
        self._index += v
        return self._index

    @property
    def index(self):
        return self._index

def gen_rndstr(s, l=6):
    import random
    return ''.join([random.choice(s) for _ in range(l)])

def md5(s):
    import hashlib
    m2 = hashlib.md5()
    m2.update(s)
    return m2.hexdigest()

def pwdhash(pwd, salt):
    '''计算加密后的密码,禁止修该函数!!!'''
    import hashlib
    return hashlib.md5(hashlib.md5(pwd).hexdigest() + hashlib.md5(salt).hexdigest()).hexdigest()

def get_querykey(query):
    return md5(str(query.query))


def parsedate(s):
    import datetime
    if isinstance(s, datetime.datetime) or isinstance(s, datetime.date):
        return s

    for f in ['%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y', '%Y%m%d', '%Y%m%d', '%Y/%m/%d',
              '%y%m%d', '%Y.%m.%d']:
        try:
            return datetime.datetime.strptime(s, f)
        except:
            pass
    return None

def isphone(phone):
    '''是否是手机格式'''
    import re
    p2 = re.compile('\d{11}')
    if p2.match(phone):
        return True
    else:
        return False

def set_cache(key, newval, timeout=30):
    from django.core.cache import cache
    v = newval() if callable(newval) else newval
    cache.set(key, '__None__' if v == None else  v, timeout)

def get_cache(key, default=None):
    from django.core.cache import cache
    v = cache.get(key, default)
    return v

def get_or_set_cache(key, newval, timeout=30):
    from django.core.cache import cache
    v = cache.get(key) if timeout else None
    if v == None:
        print 'not cache %s' % key
        v = newval() if callable(newval) else newval
        set_cache(key, v, timeout)
    if v == '__None__':
        v = None
    return v

def del_cache(key):
#     print 'del cache', key
    from django.core.cache import cache
    cache.delete(key)

def site_get_or_set_cache(key, newval, timeout=30):
    from base.siteinfo import get_site
    newkey = u'site_%s_%s' % (get_site().cachekey, key)
    return get_or_set_cache(newkey, newval, timeout)

def site_del_cache(key):
    from base.siteinfo import get_site
    newkey = u'site_%s_%s' % (get_site().cachekey, key)
    return del_cache(newkey)

def get_cached_obj(model, objid, timeout=60 * 60 * 24):
    clzname = '%s.%s' % (model.__module__, model.__name__)
    cachekey = '%s_%s' % (clzname, objid)
    def get():
        if hasattr(model, 'raw_objects'):
            objects = model.raw_objects
        else:
            objects = model.objects
        return objects.filter(id=objid).first() 
    return site_get_or_set_cache(cachekey, get, timeout=timeout)

def del_cached_obj(obj):
    if not obj.id:
        return
    model = obj.__class__
    clzname = '%s.%s' % (model.__module__, model.__name__)
    cachekey = '%s_%s' % (clzname, obj.id)
    return site_del_cache(cachekey)

def parse_time(s):
    import re
    rs = re.findall('(\d+):(\d+):(\d+)', s)
    if rs:
        rs = rs[0]
        return 60 * 60 * int(rs[0]) + 60 * int(rs[1]) + int(rs[2])
    rs = re.findall('(\d+):(\d+)', s) 
    if rs:
        rs = rs[0]
        return 60 * 60 * int(rs[0]) + 60 * int(rs[1])

def parse_datetime(s):
    import datetime
    if isinstance(s, datetime.datetime) or isinstance(s, datetime.date):
        return s
    for f in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M:%S', '%Y/%m/%d %H:%M']:
        try:
            return datetime.datetime.strptime(s, f)
        except:
            pass
    return None

def get_qrcode_url(text, logourl=None, corner='lt-rb'):
    return u'http://irapi.inruan.com/utils/qrcode?text=%s&corner=%s&logo=%s' % (text or '', corner or '', logourl or '')

def wrap_url(path):
    from base.siteinfo import get_site
    url = u'%s%s' % (get_site().siteurl, path)
    return url

def get_urlqrcode_url(path, logo):
    from base.siteinfo import get_site
    url = u'%s%s' % (get_site().siteurl, path)
    return get_qrcode_url(url, logo)

def decimalWithRate(v, r):
    from decimal import Decimal
    v = Decimal(v or 0)
    res = Decimal(v or 0)
    if r.endswith('%'):
        r = r.strip('%')
        res = v * int(float(r) * 100) / 10000
    elif r.isdigit():
        res = int(float(r) * 100) / 100
    return res

def month_first_day(y, m):
    return 1

def month_last_day(y, m):
    arr = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    d = arr[m] if m < 13 else None
    if m == 2 and y % 4 == 0 and (y % 100 != 0 or y % 400 == 0):
        d += 1
    return d

def last_month_first_day(today=None):
    import datetime
    if not today:
        today = datetime.date.today()
    month = (today.month - 1) if today.month > 1 else 12
    year = today.year - (1 if month == 12 else 0)
    return datetime.date(year, month, 1)

def get_models_text(modelname, ids, attr='name', split=','):
    '''获取模型文本'''
    def get():
        nids = splitstrip(ids, ',')
        if nids:
            from xadmin.api import AdminApiView
            model = AdminApiView().get_model(modelname)
            query = model.objects.filter() if not hasattr(model, 'raw_objects') else model.raw_objects.filter()
            return split.join([getattr(r, attr) for r in query.filter(pk__in=nids)])
    rawkey = 'get_models_text_%s_%s_%s_%s' % (modelname, ids, attr, split)
    key = md5(rawkey.lower())
    return get_or_set_cache(key, get, timeout=30)

def get_city_childrenids(ids):
    '''获取城市ID列表'''
    ids = splitstrip(ids, ',')
    def get():
        cids = set()
        if ids:
            from preset.models import Area
            for a in Area.objects.filter(id__in=ids):
                cids.add(a.id)
                for cid in a.get_subidarray():
                    cids.add(cid)
        return list(cids)
    rawkey = 'get_city_childrenids_%s' % ','.join(ids)
    key = md5(rawkey.lower())
    return get_or_set_cache(key, get, timeout=60 * 60 * 24)

def get_order_statis(orderitems):
    '''获取订单统计'''
    from preset.models import Attribute, PProduct
    res = []
    resd = {}
    odids = set()
    for oi in orderitems:
        atb = get_cached_obj(Attribute, oi.attribute_id)
        key = '%s.%s.%s.%s.%s' % (oi.pproduct_id, atb.level_id, atb.color_id, atb.maturity_id, atb.norm_id)
        odids.add(oi.order_id)
        if key not in resd:
            pproduct = get_cached_obj(PProduct, oi.pproduct_id)
            st = {
                'pproduct_id': pproduct.id,
                'pproduct': pproduct,
                'attribute': atb,
                'quantity': 0,
                'count': 0,
                'key': '%s%s'%(pproduct.id * 1000, atb.level_id),
                'sumprice': 0,
                }
            resd[key] = st
            res.append(st)
        else:
            st = resd[key]
        st['quantity'] += oi.quantity
        st['count'] += 1
        st['sumprice'] += oi.sumprice
    sumd = {
        'quantity':0,
        'count':len(odids),
        'sumprice':0,
        }
    for st in res:
        sumd['quantity'] += st['quantity']
#         sumd['count'] += st['count']
        sumd['sumprice'] += st['sumprice']
        st['meanprice'] = st['sumprice'] / st['quantity'] if st['quantity'] else 0
    sumd['meanprice'] = sumd['sumprice'] / sumd['quantity'] if sumd['quantity'] else 0
    res.sort(key=lambda st:st['key'])
    return {
        'sum':sumd,
        'items':res
        }

def get_or_set_file(filekey, content):
    '''将文件保存到上传临时目录'''
    from django.conf import settings
    import os, time
    cachepath = os.path.join(settings.CACHE_ROOT, time.strftime('%Y%m'))
    if not os.path.exists(cachepath):
        os.makedirs(cachepath)
    filepath = os.path.join(cachepath, filekey)
    if not os.path.exists(filepath):
        if callable(content):
            content = content()
        with open(filepath, 'wb') as f:
            f.write(content)
    return filepath

def wrap_signature(signature):
    from django.conf import settings
    import os
    import base64
    tag = 'base64,'
    ix = signature.find(tag) if signature else -1
    if ix >= 0:
        try:
            filekey = md5(signature)
            sigpath = os.path.join(settings.MEDIA_ROOT, 'signatures', filekey[0:3], filekey[3:6])
            sigfile = os.path.join(sigpath, '%s.svg' % filekey)
            if not os.path.exists(sigpath):
                os.makedirs(sigpath)
            if not os.path.exists(sigfile):
                b64 = signature[ix + len(tag):]
                data = base64.b64decode(b64)
                with open(sigfile, 'wb') as f:
                    f.write(data)
            res = sigfile.replace(settings.BASE_DIR, '').replace('\\', '/')
            return res
        except:
            import traceback
            traceback.print_exc()
    return signature

def fillto(arr, count):
    arr = [a for a in arr]
    if count > len(arr):
        for _ in range(count - len(arr)):
            arr.append(None)
    return arr


import re
rnorm = re.compile(r'([\d\.]*)(\S*)/(\S+)')
normdic = {}
def get_quantitytext_by_normtext(v, nv):
    '''换算数量，如v=10 nv=10枝/扎 换算结果为100枝'''
    if nv:
        if nv not in normdic:
            rs = rnorm.findall(nv)
            if rs:
                rs = rs[0]
                try:
                    q = float(rs[0] or '1')
                    if int(q) == q:
                        q = int(q)
                except:
                    q = 1
                t = rs[1]
                p = rs[2]
            else:
                q = 1
                t = nv
                p = ''
            if t == u'若干枝':
                t = p
            normdic[nv] = (q, t, p)
            print nv, q, t, p
        else:
            q, t, p = normdic[nv]
        return '%s%s' % (v * q, t)
    else:
        return '0'


def get_quantitytext_by_attribute(v, atb):
    return get_quantitytext_by_normtext(v, atb and atb.norm and atb.norm.value)


def valid_with_now(start, end, now=None):
    if not now:
        now = datetime.now()
    return (not start or parse_datetime(start) <= now) and (not end or now <= parse_datetime(end))


def get_urlqrcode_url_with_site_logo(path):
    from base.siteinfo import get_site
    logo = get_site().setting.get('img_web')
    if logo:
        logo = wrap_url(logo)
    return get_urlqrcode_url(path, logo)


if __name__ == '__main__':
    print parse_time('24:00:00')
    print parse_time('12:00:00')
    print parse_datetime('2016-11-12 18:56:54')
    print parse_datetime('2016-11-12 12:56')
    print parse_datetime('2016/11/12 12:56')
    print parse_datetime('2016/11/12 12:56')
