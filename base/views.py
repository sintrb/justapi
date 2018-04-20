# -*- coding: UTF-8 -*
'''
Copyright 2015 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2015-7-22

@author: Robin
'''
from django.conf.urls import patterns
from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import django.views.generic.base as dj
from django.conf import settings
from utils import json_filed_default
import json, re, os


class Privilege(object):
    TagStarts = 'has_'

    def __init__(self, view):
        self.view = view

    def has(self, nk):
        from siteinfo import get_site
        pvs = get_site().privileges
        if nk not in pvs or (set(self.view.get_roles()) & set(pvs[nk])):
            return True
        else:
            return False

    def __getattr__(self, k):
        if k.startswith(Privilege.TagStarts):
            global site
            nk = k[len(Privilege.TagStarts):]
            return self.has(nk)
        return object.__getattr__(self, k)


from base.siteinfo import Site


class BaseView(dj.View):
    me = None
    meid = None
    privilege = None

    translate = lambda s, x: x
    lang = settings.MAIN_LANG

    site = Site()

    checker = None

    @property
    def site(self):
        from siteinfo import get_site
        return get_site()

    def get_session(self):
        return self.request.session

    def session_get(self, k):
        return self.get_session()[k] if k in self.get_session() else None

    def session_del(self, k):
        if k in self.get_session(): del self.get_session()[k]

    def session_set(self, k, v):
        self.get_session()[k] = v

    def session_get_once(self, k):
        v = self.session_get(k)
        self.session_del(k)
        return v

    # 用户
    # me
    def get_wmeid(self):
        '''获取当前会员用户ID'''
        sme = self.session_get('me')
        if sme:
            return sme['id']
        else:
            return None

    def get_wme(self):
        '''获取当前会员用户'''
        from user.models import User
        if self.me:
            return self.me
        self.meid = self.get_wmeid()
        if self.meid:
            self.me = User.objects.filter(pk=self.meid, status=User.STATUS_NORMAL).first()
            if self.me:
                self.set_wme(self.me)
            else:
                self.session_del('me')
            return self.me
        else:
            return None

    def set_wme(self, user):
        '''设置当前登录的用户'''
        self.session_set('me', user.simple_json)
        self.session_set('mobile', user.username)
        return user

    # xme
    def get_xmeid(self):
        '''获取当前管理员用户ID'''
        sme = self.session_get('xme')
        if sme:
            return sme['id']
        else:
            return None

    def get_xme(self):
        '''获取当前管理员用户'''
        from xadmin.models import XUser
        if self.me:
            return self.me
        self.meid = self.get_xmeid()
        if self.meid:
            self.me = XUser.objects.filter(pk=self.meid, status=XUser.STATUS_NORMAL).first()
            if self.me:
                self.session_set('xme', self.me.get_json())
            else:
                self.session_del('xme')
            return self.me
        else:
            return None

    # End 用户

    def dispatch(self, request, *args, **kwargs):
        self.me = None
        self.meid = None
        if '_source' in request.GET:
            self.session_set('from_source', request.GET['_source'])
        if '_promote_user_id' in request.GET:
            self.session_set('promote_user_id', request.GET['_promote_user_id'])
        if hasattr(self, 'operation') and self.operation and not self.checkOperation(self.operation):
            print 'operation err'
        return dj.View.dispatch(self, request, *args, **kwargs)

    def is_weixin(self):
        ua = self.get_useragent()
        return 'MICROMESSENGER' in ua

    def is_wap(self):
        ua = self.get_useragent()
        return 'MOBILE' in ua

    def is_app(self):
        ua = self.get_useragent()
        return 'WEBVIEW' in ua

    def is_www(self):
        ua = self.get_useragent()
        return 'MOBILE' not in ua

    def is_huayi(self):
        ua = self.get_useragent()
        return 'FANWE_APP_SDK' in ua

    def is_wxa(self):
        ua = self.get_useragent()
        return 'MINIPROGRAM' in ua or 'wxa' in self.platform

    def get_useragent(self):
        return self.request.META['HTTP_USER_AGENT'].upper() if 'HTTP_USER_AGENT' in self.request.META else ''
    
    def get_currenturl(self):
        request = self.request
        url = '%s://%s%s' % (self.site.cheme, request.get_host(), request.get_full_path())
        return url
    
    def get_model(self, modelname):
        modelname = modelname.lower()
        from base.models import DataDic
        m = {
            'datadic': DataDic,
        }.get(modelname)
        if not m:
            raise Exception(u'不存在模型:%s' % modelname)
        return m

    def get_ip(self):
        if 'HTTP_X_REAL_IP' in self.request.META:
            return self.request.META['HTTP_X_REAL_IP'].split(',')[-1]
        if 'HTTP_X_FORWARDED_FOR' in self.request.META:
            return self.request.META["HTTP_X_FORWARDED_FOR"].split(',')[-1]
        return self.request.META.get("REMOTE_ADDR", None)

    def get_clientkey(self):
        from base.utils import md5
        key = md5(str(self.meid or self.request.session.session_key or self.get_ip()))
        return key

    def get_platform(self):
        from stslog.models import PLATFORM_APP, PLATFORM_WX, PLATFORM_PC, PLATFORM_NONE, PLATFORM_WAP
        return self.is_app() and PLATFORM_APP or self.is_weixin() and PLATFORM_WX or self.is_wap() and PLATFORM_WAP or self.is_www() and PLATFORM_PC or PLATFORM_NONE

    @property
    def platform(self):
        return self.request.POST.get('_platform') or self.request.COOKIES.get('_platform') or self.request.GET.get('_platform') or self.session_get('_platform') or str(self.get_platform())

    @property
    def token(self):
        return self.request.POST.get('_token') or self.request.COOKIES.get('_token') or self.request.GET.get('_token')

apiindex = 0


def asapi(logined=True, userrole=None, operation=None, checker=None, timegap=0, data=None, cachetime=0, tag=None):
    def _func(func):
        def __func(self, *args, **kvagrs):
            return func(self, *args, **kvagrs)

        global apiindex
        import inspect
        argspec = inspect.getargspec(func)
        setattr(__func, 'argspec', argspec)
        setattr(__func, 'doc', inspect.getdoc(func))
        setattr(__func, 'logined', logined)
        setattr(__func, 'userrole', userrole)
        setattr(__func, 'operation', operation)
        setattr(__func, 'checker', checker)
        setattr(__func, 'timegap', timegap)
        setattr(__func, 'apiindex', apiindex)
        setattr(__func, 'data', data)
        setattr(__func, 'cachetime', cachetime)
        setattr(__func, 'tag', tag)
        from base.defs import ApiParam
        funcagrs = argspec.args
        defaults = argspec.defaults
        args = []
        argslen = len(funcagrs) - (len(defaults) if defaults else 0) - 1
        for i, k in enumerate(funcagrs[1:]):
            arg = {
                'name': k
            }
            if i >= argslen:
                dval = defaults[i - argslen]
                if isinstance(dval, ApiParam):
                    info = dval
                else:
                    info = ApiParam(default=dval, empty=True)
                arg['info'] = info
            else:
                arg['info'] = ApiParam()
            if k == '_param':
                arg['info'].name = '不确定参数'
            args.append(arg)
        setattr(__func, 'arginfos', args)
        apiindex += 1
        return __func

    return _func


class ApiView(BaseView):
    def api_response(self, v):
        res = HttpResponse(json.dumps(v, default=json_filed_default), content_type="text/json")
        return res

    def doc(self, request):
        apis = []
        tagmap = {}
        tags = []
        for an in dir(self.__class__):
            at = getattr(self.__class__, an)
            if hasattr(at, 'logined'):
                from base.utils import splitstrip
                apifun = at
                doc = getattr(apifun, 'doc')
                arginfos = [ai for ai in getattr(apifun, 'arginfos') if ai['name'] != '_param']
                userrole = getattr(apifun, 'userrole')
                tag = getattr(apifun, 'tag')
                fund = {
                    'name': an,
                    'doc': doc,
                    'args': arginfos,
                    'arglen': len(arginfos),
                    'userrole': userrole if type(userrole) in (list, tuple, set) else (
                    [userrole, ] if userrole else None),
                    'operation': splitstrip(getattr(apifun, 'operation') or '', '__or__'),
                    'logined': getattr(apifun, 'logined'),
                    'timegap': getattr(apifun, 'timegap'),
                    'apiindex': getattr(apifun, 'apiindex'),
                    'data': getattr(apifun, 'data'),
                }
                apis.append(fund)
                if tag:
                    if ':' in tag:
                        ts = tag.split(':')
                        tag = ts[0].strip()
                        tagname = ts[1].strip()
                    else:
                        tagname = None
                    if tag not in tagmap:
                        tagd = {
                            'tag': tag,
                            'name': tagname or '',
                            'apis': []
                        }
                        tagmap[tag] = tagd
                        tags.append(tagd)
                    else:
                        tagd = tagmap[tag]
                    if tagname:
                        tagd['name'] = tagname
                    tagd['apis'].append(fund)
        from django.template import Template, Context
        if request.GET.get('tag'):
            tag = tagmap.get(request.GET.get('tag'))
            apis = tag['apis']
        else:
            tag = None
        apis.sort(key=lambda x: x['apiindex'])
        cxt = {'apis': apis, 'template_name': 'utils/apidoc.html', 'tags': tags, 'tag': tag}
        return HttpResponse(
            content=Template(open(os.path.join(settings.BASE_DIR, 'templates', 'utils', 'apidoc.html')).read()).render(
                Context(cxt)))

    def get(self, request, apiname, *k, **ks):
        import time
        from utils import Data
        from defs import raiseApiEx as err
        from defs import ApiException, CheckException
        self.me = None
        self.meid = None
        starttime = time.time()
        try:
            apiname = apiname.strip('/')
            sys_debug = self.site.setting.get('sys_debug')
            if sys_debug and (apiname == 'doc.html' or not apiname) and self.session_get('xme'):
                return self.doc(request)
            if not sys_debug and request.method != 'POST':
                err("Not Allow!")
            if not apiname:
                err("接口不能为空")
            apifun = None
            try:
                apifun = getattr(self, apiname)
                needlogin = getattr(apifun, 'logined')
            except:
                err("不存在接口 %s" % apiname)

            needlogin = getattr(apifun, 'logined')
            userrole = getattr(apifun, 'userrole')
            operation = getattr(apifun, 'operation')
            checker = getattr(apifun, 'checker')
            timegap = getattr(apifun, 'timegap')
            cachetime = getattr(apifun, 'cachetime')
            if timegap:
                from django.core.cache import cache
                cachekey = 'nexttime_%s_%s_%s' % (self.get_clientkey(), self.__class__.__name__, apiname)
                nexttime = cache.get(cachekey)
                if nexttime and time.time() < nexttime:
                    # err(u'调用太频繁:%s' % (cachekey if sys_debug else apiname))
                    err(u'调用太频繁')
                cache.set(cachekey, time.time() + timegap)
            if needlogin and not self.get_meid():
                err(u'用户未登录', c=2001)

            if userrole and userrole not in self.get_roles():
                err(u'用户权限不足')

            if operation:
                self.checkOperation(operation)

            if checker and not checker(self, request):
                err(u'检查不通过')

            kvargs = {}
            param = {}
            param.update(dict(request.GET.items()))
            param.update(dict(request.POST.items()))

            missargs = []
            arginfos = getattr(apifun, 'arginfos')
            for p in arginfos:
                ap = p['info']
                name = p['name']
                #                 print name, ap.default, ap.empty, ap.hasdefault
                if name != '_param' and ap.empty and name not in param:
                    param[name] = ap.default if ap.hasdefault else ''
                if name == '_param':
                    kvargs[name] = param
                elif not ap.hasdefault and name not in param:
                    missargs.append(name)
                elif not ap.hasdefault and not ap.empty and not param.get(name):
                    missargs.append(name)
                else:
                    kvargs[name] = param.get(name, ap.default)
            if missargs:
                err(u'缺失参数: %s' % (', '.join(missargs)))

            def doapi():
                data = apifun(**kvargs)
                if isinstance(data, Data):
                    data = data.data
                return data

            if cachetime:
                from base.utils import get_or_set_cache, md5
                paramkey = u'&'.join([u'%s=%s' % (k, v) for k, v in param.items() if not k.startswith('_')])
                apikey = 'api_cache_%s_%s' % (apiname, md5(paramkey))

                def responsejson():
                    data = get_or_set_cache(apikey, doapi, cachetime)
                    res = {"code": 0, "data": data} if (not data or type(data) != dict or '_msg' not in data) else {
                        "code": 0, "msg": data['_msg'], "data": data.get('data')}
                    res['timestamp'] = int(time.time())
                    return json.dumps(res, default=json_filed_default)

                data = HttpResponse(get_or_set_cache(apikey + '_json', responsejson, cachetime),
                                    content_type="text/json")
            else:
                data = doapi()
            from django.http.response import HttpResponseBase
            if isinstance(data, HttpResponseBase):
                return data
            res = {"code": 0, "data": data} if (not data or type(data) != dict or '_msg' not in data) else {"code": 0,
                                                                                                            "msg": data[
                                                                                                                '_msg'],
                                                                                                            "data": data.get(
                                                                                                                'data')}
            res['time'] = int((time.time() - starttime) * 1000)
            return self.api_response(res)

        except ApiException, e:
            res = e.args[0]
            if 'msg' in res:
                res['msg'] = self.translate(res['msg'])
            return self.api_response(res)
        except CheckException, e:
            res = {"code": -1, "msg": self.translate(e.message)}
            return self.api_response(res)

    def post(self, request, *k, **ks):
        return self.get(request, *k, **ks)

    def delete(self, request, *k, **ks):
        return self.get(request, *k, **ks)

    def put(self, request, *k, **ks):
        return self.get(request, *k, **ks)


def dispatch(self, request, *args, **kwargs):
    if self.site.setting.get('sitemaintaining') and not request.path.startswith('/xadmin'):
        return self.render_to_response(request, templ='error.html', cxt={'stopback': True, 'err': u'系统维护中...'})
    if self.logined and not self.get_meid():
        self.session_set('logingoto', request.path)
        wxinfo = self.session_get('wx')
        if self.is_weixin() and not self.is_wxa():
            if wxinfo and wxinfo.get('openid'):
                from user.models import User
                user = User.objects.filter(openid=wxinfo.get('openid')).first()
                if user:
                    self.set_wme(user)
                    if self.get_meid():
                        return BaseView.dispatch(self, request, *args, **kwargs)
            else:
                return HttpResponseRedirect('/wx/startauth')
                #         http://127.0.0.1:8080/external/pay/?money=0.1&title=%E6%94%AF%E4%BB%98&notifyurl=http://www.baidu.com?x=2&returnurl=http://www.qq.com&appid=I149943514903&tradeno=2338
        self.session_set('logingoto', request.get_full_path())
        return HttpResponseRedirect('/login.html' if not hasattr(self, 'loginurl') else getattr(self, 'loginurl'))
    elif self.checker:
        if hasattr(self.checker, 'im_self'):
            if self.checker.im_self and not self.checker(request):
                raise Exception('检查不通过')
        elif not self.checker(self, request):
            raise Exception('检查不通过')
    if request.GET and request.GET.get('_platform'):
        self.session_set('_platform', request.GET.get('_platform'))
    return BaseView.dispatch(self, request, *args, **kwargs)


def asview(logined=True, userrole=None, operation=None, checker=None, loginurl=None):
    def _auth(viewclz, *args, **kvagrs):
        if logined or userrole:
            setattr(viewclz, 'logined', True)
        if userrole:
            setattr(viewclz, 'userrole', userrole)
        if operation:
            setattr(viewclz, 'operation', operation)
        if checker:
            setattr(viewclz, 'checker', checker)
        if loginurl:
            setattr(viewclz, 'loginurl', loginurl)
        return viewclz

    return _auth


class PageView(BaseView):
    logined = False
    userrole = None
    operation = None
    content_type = 'text/html'
    template_name = None
    error_template_name = 'error.html'

    def dispatch(self, request, *args, **kwargs):
        from defs import CheckException, PageException
        try:
            return dispatch(self, request, *args, **kwargs)
        except CheckException, e:
            return self.render_to_response(request, self.error_template_name,
                                           cxt={'error': e.message, 'stopback': True})
        except PageException, e:
            return self.render_to_response(request, self.error_template_name, cxt={'error': e.message, 'backurl': e.goto, 'stopback': e.stopback})

    def render(self, request, templ, cxt):
        if cxt == None:
            cxt = {
                'template_name': templ
            }
        else:
            cxt['template_name'] = templ
        cxt['site'] = self.site
        cxt['view'] = self
        cxt['view_name'] = self.__class__.__name__
        cxt['privilege'] = self.privilege
        cxt['STATIC_URL'] = '/static/'
        # 多语言
        lang = self.lang
        ng = self.site.get_template_engines(lang)
        from django.template import Context
        cxt['lang'] = self.lang
        content = ng.get_template(templ).render(Context(cxt))
        return HttpResponse(content=content)

    def render_to_response(self, request, templ=None, cxt=None):
        if templ == None:
            templ = self.get_template_name()

        return self.render(request, templ, cxt)

    def get_template_name(self):
        return self.template_name

    def get(self, request):
        return self.render_to_response(request)

    def raiseErr(self, err):
        from base.defs import PageException
        raise PageException(err)


class AutoTemplView(PageView):
    def render(self, request, templ, cxt):
        if self.is_wap() and not templ.startswith('wap'):
            templ = 'wap/%s' % templ
        else:
            templ = 'www/%s' % templ
        if cxt == None:
            cxt = {}
        cxt['view'] = self
        return PageView.render(self, request, templ, cxt)


class RequestTempView(AutoTemplView):
    def get(self, request, templ):
        return self.render_to_response(request, templ)


class WapPageView(AutoTemplView):
    def is_wap(self):
        return True


class WebPageView(AutoTemplView):
    def is_www(self):
        return True

    def is_wap(self):
        return False


class WXPageView(WebPageView):
    pass


class UploadView(PageView):
    def get(self, request):
        return self.render_to_response(request, "utils/upload.html")

    def handleupload(self, data, filename, content_type=None):
        import time, random
        if content_type and filename == 'blob' and 'jpeg' in content_type:
            filename = '%s.jpg' % int(time.time())
        ix = filename.rfind('.')
        if ix >= 0:
            sufix = filename[ix:]
            name = filename[0:ix]
        else:
            sufix = ''
            name = filename
        sufix = sufix.lower()
        pdir = time.strftime('%Y%m')
        pname = time.strftime('%Y%m%d%H%M%S')
        pname = pname + '_%02d%s' % (random.randint(0, 100), sufix)
        rdir = os.path.join('file', pdir)
        rname = os.path.join(rdir, pname)
        apdir = os.path.join(settings.MEDIA_ROOT, rdir)
        apname = os.path.join(apdir, pname)
        if not os.path.exists(apdir):
            os.makedirs(apdir)
        size = len(data)
        with open(apname, 'wb') as f:
            f.write(data)
        url = '%s%s/%s/%s' % (settings.MEDIA_URL, 'file', pdir, pname)
        fileinfo = [{'url': u'%s%s' % (
        self.site.setting.get('irfile_upload_useabs') and self.site.setting.get('irfile_upload_baseurl').rstrip(
            '/') or '', url.replace('\\', '/')), 'file': rname, 'filename': filename, 'name': name, 'size': size}]
        #             res = {'success':True, 'count':1, 'files':fileinfo}
        r = HttpResponse(json.dumps(fileinfo))
        r['Access-Control-Allow-Headers'] = ''
        r['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, POST'
        r['Access-Control-Allow-Origin'] = '*'
        return r

    def post(self, request):
        fl = request.FILES['upload_file'] if 'upload_file' in request.FILES else (
        request.FILES['file'] if 'file' in request.FILES else None)
        filename = request.POST['filename'] if 'filename' in request.POST else None
        if fl:
            return self.handleupload(fl.read(), filename or fl.name, fl.content_type)
        elif 'file' in request.POST:
            import base64
            data = base64.decodestring(request.POST['file'])
            return self.handleupload(data, filename)
        else:
            return HttpResponse('no file')

    def options(self, request, *args, **kwargs):
        r = HttpResponse()
        r['Access-Control-Allow-Headers'] = ''
        r['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, POST'
        r['Access-Control-Allow-Origin'] = '*'
        return r


class PostUploadView(PageView):
    def post(self, request):
        import random
        import time
        import base64

        filename = request.POST['name']
        data = base64.decodestring(request.POST['file'])
        ix = filename.rfind('.')
        if ix >= 0:
            sufix = filename[ix:]
            name = filename[0:ix]
        else:
            sufix = ''
            name = filename
        sufix = sufix.lower()
        pdir = time.strftime('%Y%m')
        pname = time.strftime('%Y%m%d%H%M%S')
        pname = pname + '_%02d%s' % (random.randint(0, 100), sufix)
        rdir = os.path.join('file', pdir)
        rname = os.path.join(rdir, pname)
        apdir = os.path.join(settings.MEDIA_ROOT, rdir)
        apname = os.path.join(apdir, pname)
        if not os.path.exists(apdir):
            os.makedirs(apdir)
        size = len(data)
        #         print apname
        with open(apname, 'wb') as f:
            f.write(data)
        url = '%s%s/%s/%s' % (settings.MEDIA_URL, 'file', pdir, pname)
        fileinfo = [{'url': url.replace('\\', '/'), 'file': rname, 'filename': filename, 'name': name, 'size': size}]
        res = {'success': True, 'count': 1, 'files': fileinfo}
        return HttpResponse(json.dumps(res))


class CaptchaView(PageView):
    def get(self, request):
        from DjangoCaptcha import Captcha
        import random
        l = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        s = random.sample(l, 4)
        ca = Captcha(request)
        ca.words = [''.join(s)]
        ca.img_width = 120
        ca.img_height = 30
        ca.type = 'word'
        self.is_weixin()
        return ca.display()

    @staticmethod
    def check(request, code=None):
        from base.siteinfo import get_site
        if get_site().sys_debug and code == "8888":
            return True
        from DjangoCaptcha import Captcha
        ca = Captcha(request)
        return ca.check(code)


class EnvView(PageView):
    def get(self, request):
        envs = (
            ("is_wap", self.is_wap()),
            ("is_www", self.is_www()),
            ("is_weixin", self.is_weixin()),
        )
        return self.render_to_response(request, "utils/env.html", cxt={"envs": envs})


class UploadHandlerView(dj.View):
    document_root = None
    image_max_size = 1024 * 1024 * 2.5
    image_max_height = 1600
    image_max_width = 1600
    image_watermark_size = 1024 * 100
    watermark_file = 'static/img/watermark.png'
    rwh = re.compile('(\d+)x(\d+)')

    def handleImage(self, rawpath, newpath, arg):
        try:
            print 'handle', arg, rawpath, '->', newpath
            try:
                import Image
            except:
                pass
            try:
                from PIL import Image
            except:
                pass
            im = Image.open(rawpath)
            if hasattr(im, '_getexif'):
                exif = im._getexif()
                if exif and exif.get(0x0112, 1) != 1:
                    # 需要旋转
                    r = exif.get(0x0112)
                    rd = {
                        1: 0,
                        6: -90,
                        8: 90,
                        3: 180
                    }
                    print 'Orientation:', r, ' angle:', rd.get(r) or 'unknow'
                    if r in rd:
                        im = im.rotate(rd.get(r))

            w, h = im.size
            if arg == 'small':
                k = float(h) / float(w)
                w = 200
                h = int(w * k)
                newimg = im.resize((w, h), )
                newimg.save(newpath, quality=100)
                return newpath
            elif arg == 'normal':
                k = float(h) / float(w)
                nw = self.image_max_width or 500
                nh = self.image_max_height or 500
                nk = float(nh) / float(nw)
                if nk > k:
                    w = nw
                    h = int(w * k)
                else:
                    h = nh
                    w = int(h / k)
                newimg = im.resize((w, h), )
                newimg.save(newpath, quality=100)
                return newpath
            elif arg == 'watermark':
                wmfile = os.path.join(settings.BASE_DIR, self.watermark_file)
                if os.path.exists(wmfile):
                    wm = Image.open(wmfile)
                    newwm = wm.resize((w, h), )
                    im = Image.composite(newwm, im, newwm)
                    im.save(newpath, quality=100)
                    return newpath
                else:
                    return rawpath
            elif arg == 'resize':
                k = float(h) / float(w)
                nw = self.image_max_width or 1000
                nh = self.image_max_height or 1000
                nk = float(nh) / float(nw)
                if nk > k:
                    w = nw
                    h = int(w * k)
                else:
                    h = nh
                    w = int(h / k)
                newimg = im.resize((w, h), )
                newimg.save(newpath, quality=100)
                return newpath
            else:
                rs = UploadHandlerView.rwh.findall(arg)
                if rs:
                    r = rs[0]
                    #                     im.thumbnail((int(r[0]),int(r[1])))
                    nw = int(r[0])
                    nh = int(r[1])
                    k = float(h) / float(w)
                    nk = float(nh) / float(nw)
                    if nk > k:
                        ch = h
                        cw = ch / nk
                    elif nk < k:
                        cw = w
                        ch = cw * nk
                    else:
                        cw = w
                        ch = h
                    cw, ch = int(cw), int(ch)
                    if cw != w or ch != h:
                        r = ((w - cw) / 2, (h - ch) / 2, w - (w - cw) / 2, h - (h - ch) / 2)
                        im = im.crop(r)

                    newimg = im.resize((nw, nh))
                    newimg.save(newpath, quality=100)
                    return newpath
                else:
                    return rawpath
        except Exception, e:
            print '%s : %s' % (e, rawpath)
            return rawpath

    def get(self, request, path):
        import posixpath
        from urllib import unquote
        arg = request.GET.get('type', '')
        path = posixpath.normpath(unquote(path)).lstrip('/')
        abspath = os.path.join(self.document_root, *path.split('/'))
        force = request.GET.get('force')
        if os.path.isfile(abspath):
            document_root, path = os.path.split(abspath)
            _, ext = os.path.splitext(path)
            if ext.lower() in ['.png', '.jpeg', '.jpg', '.bmp', '.gif']:
                # handle image
                if self.image_max_size and os.path.getsize(abspath) > self.image_max_size and arg != 'resize':
                    document_root, path = os.path.split(abspath)
                    name, ext = os.path.splitext(path)
                    resizeabspath = os.path.join(document_root, u'%s-%s%s' % (name, 'resize', ext))
                    if force or not os.path.exists(resizeabspath) or os.stat(abspath).st_mtime > os.stat(
                            resizeabspath).st_mtime:
                        abspath = self.handleImage(abspath, resizeabspath, 'resize')
                    else:
                        abspath = resizeabspath
                if arg:
                    # need handle
                    document_root, path = os.path.split(abspath)
                    name, ext = os.path.splitext(path)
                    newabspath = os.path.join(document_root, u'%s-%s%s' % (name, arg, ext))
                    if force or not os.path.isfile(newabspath) or os.stat(abspath).st_mtime > os.stat(
                            newabspath).st_mtime:
                        abspath = self.handleImage(abspath, newabspath, arg)
                    else:
                        abspath = newabspath
                if self.watermark_file and (
                    'watermark' in request.GET):  # or os.path.getsize(abspath) > self.image_watermark_size):
                    document_root, path = os.path.split(abspath)
                    name, ext = os.path.splitext(path)
                    watermarkabspath = os.path.join(document_root, u'%s-%s%s' % (name, 'watermark', ext))
                    if force or not os.path.exists(watermarkabspath) or os.stat(abspath).st_mtime > os.stat(
                            watermarkabspath).st_mtime:
                        abspath = self.handleImage(abspath, watermarkabspath, 'watermark')
                    else:
                        abspath = watermarkabspath
                if self.watermark_file and 'watermark' not in abspath:
                    document_root, path = os.path.split(abspath)
                    name, ext = os.path.splitext(path)
                    watermarkabspath = os.path.join(document_root, u'%s-%s%s' % (name, 'watermark', ext))
                    if os.path.exists(watermarkabspath):
                        abspath = watermarkabspath

            from django.views import static
            document_root, path = os.path.split(abspath)
            res = static.serve(request, path, document_root, settings.DEBUG)
            if 'attname' in request.GET:
                res['Content-Disposition'] = 'attachment;filename="{0}"'.format(request.GET['attname'])
                res['Content-Type'] = 'application/octet-stream'
            return res
        else:
            from django.http import Http404
            raise Http404


class WxaCodeView(BaseView):
    '''获取小程序码，使用官方接口B, 传入参数:page scene'''
    def get(self, request):
        from django.views import static
        from django.conf import settings
        from base.utils import get_or_set_file, md5
        param = {
            'page':request.GET.get('page', ''),
            'scene':request.GET.get('scene', ''),
            }
        key = md5(self.site.wxa_instance.appid + '?' + u'&'.join([u'%s=%s'%(k, v) for k,v in param.items()]))
        def get():
            return self.site.wxa_instance.get_wxacode_unlimit(param).content
        filepath = get_or_set_file('%s.png' % key, get)
#         print filepath.replace(settings.BASE_DIR, '')
        document_root, path = os.path.split(filepath)
        res = static.serve(request, path, document_root, settings.DEBUG)
        if 'attname' in request.GET:
            res['Content-Disposition'] = 'attachment;filename="{0}"'.format(request.GET['attname'])
            res['Content-Type'] = 'application/octet-stream'
        else:
            res['Content-Type'] = 'image/png'
        res['Content-Key'] = key
        return res
        

urlpatterns = patterns('',
                       (r'^utils/post\.html$', csrf_exempt(PostUploadView.as_view())),
                       (r'^utils/upload\.html$', csrf_exempt(UploadView.as_view())),
                       #     (r'^utils/upload\.html$', csrf_exempt(UploadView.as_view())),
                       (r'^utils/uploadtest\.html$', PageView.as_view(template_name="utils/uploadtest.html")),
                       (r'^utils/verifycode\.gif', CaptchaView.as_view()),
                       (r'^utils/env\.html$', EnvView.as_view()),
                       (r'^utils/wxacode$', WxaCodeView.as_view()),
                       (r'^upload/(?P<path>.*)$',
                        UploadHandlerView.as_view(document_root=os.path.join(settings.BASE_DIR, 'upload'))),
                       )
