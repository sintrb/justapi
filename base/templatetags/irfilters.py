# -*- coding: UTF-8 -*
'''
Copyright 2015 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2015-8-17

@author: Robin
'''

from django import template
register = template.Library()

@register.filter
def to2d(arr, cols):
    from third.arrutils import to_2d_array
    return to_2d_array(arr, cols)

@register.filter
def least(arr, count):
    if arr == None:
        return []
    l = arr.count() if hasattr(arr, 'count') and type(arr) not in [list, tuple] else len(arr)
    count = int(count)
    if l and l < count:
        arr = [a for a in arr] if arr != None else []
        return (arr * ((count + 1) / l * l))[0:count]
    else:
        return arr

@register.filter
def most(arr, count):
    if arr == None:
        return []
    l = arr.count() if hasattr(arr, 'count') else len(arr)
    count = int(count)
    if l and l > count:
        return arr[0:count]
    else:
        return arr

@register.filter
def fixed(arr, count):
    if arr == None:
        return []
    l = arr.count() if hasattr(arr, 'count') else len(arr)
    count = int(count)
    if l and l < count:
        arr = [a for a in arr] if arr != None else []
        return (arr * ((count + 1) / l * l))[0:count]
    elif l and l > count:
        return arr[0:count]
    else:
        return arr

@register.filter
def unescape(v):
    import HTMLParser
    html_parser = HTMLParser.HTMLParser()
    txt = html_parser.unescape(v)
    return txt.strip()

@register.filter
def image(v, arg):
    if v:
        if not arg:
            return v
        if '://' in v:
            return u'%s!%s' % (v, arg)
        if '?' in v:
            return u'%s&type=%s' % (v, arg)
        else:
            return u'%s?type=%s' % (v, arg)
    else:
        return None

@register.filter
def firstimage(v, arg):
    if v:
        if type(v) in [list, tuple]:
            v = v[0]
        elif ';' in v:
            v = v[0:v.index(';')]
    return image(v, arg)

@register.filter
def split(v, arg=' '):
    return [s.strip() for s in v.split(arg) if s.strip()] if v else []

@register.filter
def jsondumps(v):
    import json
    from base.utils import json_filed_default
    return json.dumps(v, default=json_filed_default)

@register.filter
def strmask(value, front=True):
    front = front == "" or str(front).upper() == "True"
    l = len(value)
    ml = max(l / 2, 1) if l % 2 == 0 else (l + 1) / 2
    if front:
        msk = '*' * ml
        return "%s%s" % (value[0:max(l - ml, 1)], msk)
    else:
        msk = '*' * ml
        return "%s%s" % (msk, value[ml:])        

@register.filter
def markdown(s):
    import markdown2
    return markdown2.markdown(s) if s else None

@register.filter
def orderby(query, order_by):
    from base.utils import splitstrip
    return query.order_by(*(splitstrip(order_by, ',')))


@register.filter
def pageurl(request, page):
    import re
    curpath = request.get_full_path()
    dr = re.compile(r'page=[0-9]*', re.S)
    dd = dr.sub('', curpath)
    if '?' not in dd:
        dd = dd + '?'
    if not dd.endswith('&') and not dd.endswith('?'):
        dd = dd + '&'
    dd = dd + 'page=%s' % page
    return dd

@register.filter
def autofloat(v, count=1):
    v = float(v or '0')
    return str(round(v * 100) / 100)

@register.filter
def splitstrip(ls, seg=' '):
    '''
    使用指定分隔符分割字符串。
    "a   b c" | splitstrip:' '   ==> ['a','b','c']
    '''
    import base.utils
    return base.utils.splitstrip(ls, seg.replace('\\n', '\n'))
    
@register.filter
def timestamp(obj):
    '''
    获取时间戳
    '''
    import time, datetime
    if isinstance(obj, datetime.datetime):
        obj = obj.timetuple()
    if isinstance(obj, datetime.date):
        obj = obj.timetuple()
    if isinstance(obj, time.struct_time):
        obj = time.mktime(obj)
    return obj


@register.tag('rename')
def do_rename(parser, token):
    bits = token.contents.split()
    valuetoken = bits[1]
    newname = bits[2].strip('"\'')
    if len(valuetoken) and valuetoken[0] in '"\'':
        valuetoken = valuetoken.strip('"\'')
    else:
        valuetoken = parser.compile_filter(valuetoken)
    return RenameTag(valuetoken, newname)

class RenameTag(template.Node):
    def __init__(self, valuetoken, newname):
        self.valuetoken, self.newname = valuetoken, newname

    def render(self, context):
        if type(self.valuetoken) not in [str, unicode]:
            value = self.valuetoken.resolve(context)
        else:
            value = self.valuetoken
        context[self.newname] = value
        from django.utils.safestring import  SafeText
        return SafeText('<!- rename to %s -->' % (self.newname))

@register.tag('cache')
def do_cache(parser, token):
    import re
    bits = token.contents.split()
    rs = re.findall('([0-9]+)([dhms]*)', bits[1])
    if rs:
        t, u = rs[0]
        u = u.lower()
        if u == 'd':
            cachetime = int(t) * (60 * 60 * 24)
        elif u == 'h':
            cachetime = int(t) * (60 * 60)
        elif u == 'm':
            cachetime = int(t) * (60)
        else:
            cachetime = int(t)
    else:
        cachetime = parser.compile_filter(bits[1])
    cachekey = bits[2]
#     if len(cachekey) and cachekey[0] in '"\'':
#         cachekey = cachekey.strip('"\'')
#     else:
    cachekey = parser.compile_filter(cachekey)
    
    isdebug = bits[3] if len(bits) >= 4 else 'False'
    isdebug = parser.compile_filter(isdebug)
    
    
    nodelist = parser.parse(('endcache',))

    # This check is kept for backwards-compatibility. See #3100.
    endblock = parser.next_token()
    acceptable_endblocks = ('endcache',)
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, 'endcache', acceptable_endblocks)

    return CacheTag(cachekey, cachetime, nodelist, isdebug)

class CacheTag(template.Node):
    def __init__(self, cachekey, cachetime, nodelist, isdebug):
        self.cachekey, self.cachetime, self.nodelist, self.isdebug = cachekey, cachetime, nodelist, isdebug

    def __repr__(self):
        return "<Cache Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        import time
        if type(self.cachetime) != int:
            cachetime = self.cachetime.resolve(context)
        else:
            cachetime = self.cachetime
        if isinstance(self.cachekey, basestring):
            cachekey = self.cachekey
        else:
            cachekey = self.cachekey.resolve(context)
        
        if type(self.isdebug) != bool:
            isdebug = self.isdebug.resolve(context)
        else:
            isdebug = self.isdebug

        from base.utils import get_or_set_cache
        def get_value():
            result = self.nodelist.render(context)
            value = {
                      'result':result,
                      'time':time.time()
                      }
            return value
        value = get_or_set_cache(u'cache_%s' % cachekey, get_value, self.cachetime)
        if isdebug:
            from django.utils.safestring import  SafeText
            return SafeText('<!- cache key=%s time=%s cached@%s ttl=%s -->' % (cachekey, cachetime, int(value['time']), int(cachetime + value['time'] - time.time()))) + value['result'] + SafeText('<!- end cache key=%s -->' % (cachekey))
        else:
            return value['result']


@register.filter
def strip(s):
    '''
    去掉首尾空格。
    "   b " | strip   ==> "b"
    '''
    return s.strip() if s else s


@register.filter
def nohtml(v):
    import re
    dr = re.compile(r'<[^>]+>', re.S)
    dd = dr.sub('', v).replace('&nbsp;', ' ')
    return dd

@register.filter
def signfloat(v):
    '''根据值正负在前面加上+-号'''
    if v == 0:
        return '0'
    if v > 0:
        return u'+%s' % autofloat(v)
    else:
        return u'-%s' % autofloat(abs(v))


@register.filter
def valueat(arr, ix):
    '''返回arr的第ix个值，越界返回None'''
    return arr[ix] if arr and len(arr) > ix else None

# 下面是银软的大招

# 异步加载
@register.tag('infinite')
def do_infinite(parser, token):
    nodelist = parser.parse(('endinfinite',))

    # This check is kept for backwards-compatibility. See #3100.
    endblock = parser.next_token()
    acceptable_endblocks = ('endinfinite',)
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, 'endinfinite', acceptable_endblocks)

    return InfiniteTag(nodelist)


infinite_template = '''
<!-- start page:{{curpage}}/{{lastpage}} -->
<div class="weui-pull-to-refresh-layer">
    <div class="pull-to-refresh-arrow"></div>
    <div class="pull-to-refresh-preloader"></div>
    <div class="down">下拉刷新</div>
    <div class="up">释放刷新</div>
    <div class="refresh">正在刷新...</div>
</div>
<div class="weui-infinite-scroll">
    <div class="infinite-preloader show-when-loadding"></div>
    <span class="show-when-loadding">正在加载...</span>
    <span class="show-when-nomore" style="display:none">没有了，我是有底线的！</span>
</div>
<script>
    $(function(){
        root = $("#{{refreshid}}").parents('.weui_tab_bd').eq(0);
        inctl = root;
        rectl = inctl.find('.weui_cells').eq(0);
        //if(rectl.length == 0)
        //    rectl = root;

        var curpage = {{curpage}};
        var lastpage = {{lastpage}};
        var loading = false;  //状态标记
        var inhtml = inctl.find('.weui-infinite-scroll').html();
        var nomore = false;
        var checkfinish = function(){
            if(curpage>=lastpage){
                // 加载完毕
                // inctl.find('.weui-infinite-scroll').html('没有更多了!');
                inctl.find('.show-when-loadding').hide();
                inctl.find('.show-when-nomore').show();
                curpage = lastpage;
                nomore = true;
                return;
            }
            else{
                inctl.find('.show-when-loadding').show();
                inctl.find('.show-when-nomore').hide();
            }
        };
        var ajaxload = function(clear){
            if(loading || (!clear && nomore)) return;
            checkfinish();
            loading = true;
            //console.log("ajaxload");
            var loadpage = clear?1: curpage+1;
            var ajaxurl = B.buildParam(B.buildParam(window.location.pathname + window.location.search, "ajax", B.timestamp()), "page", loadpage);
            if(clear){
                //B.doing('正在刷新...');
                nomore = false;
            }
            $.get(ajaxurl, function(r){
                rectl.pullToRefreshDone();
                //B.done();
                
                if(clear){
                    inctl.find('.list-start').nextUntil('.list-end').remove();
                    inctl.find('.weui-infinite-scroll').html(inhtml);
                    $.toptip("已刷新","primary");
                    //B.toast("已刷新");
                }
                
                var html = r.trim();
                var jqhtml = $(html);
                if(html.length){
                    jqhtml.insertBefore(inctl.find('.list-end'));
                    curpage = loadpage;
                }
                if('infiniteAfterAjax' in window){
                    window.infiniteAfterAjax(jqhtml);
                }
                checkfinish();                
                loading = false;
            });
            return true;
        };
        
        var v = root.find(".weui-pull-to-refresh-layer");
        v.remove();
        v.insertBefore(rectl.children().eq(0));
        rectl.pullToRefresh().on('pull-to-refresh', function(){
            if(!ajaxload(true)){
                rectl.pullToRefreshDone();
            }
        });
        
        
        var v = root.find(".weui-infinite-scroll");
        v.remove();
        v.appendTo(inctl);
        inctl.infinite().on("infinite", function() {
            ajaxload();
        });
        checkfinish();
    });
</script>
<div id="{{refreshid}}" class="list-start"></div>
{{result}}
<div id="{{refreshid}}" class="list-end"></div>

'''.replace('{{', '<<').replace('{', '{{').replace('<<', '{').replace('{{', '<<').replace('}}', '>>').replace('}', '}}').replace('>>', '}').replace('}}', '>>')


class InfiniteTag(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def __repr__(self):
        return "<Cache Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        from django.utils.safestring import SafeText
        import time
        ispage = not context['view'].request.GET.get('ajax')
        pager = context['pager']
        if ispage:
            result = self.nodelist.render(context)
            refreshid = 'weui-pull-to-refresh-layer' + str(int(time.time()))
            return SafeText(infinite_template.format(lastpage=pager['lastpage'], curpage=pager['page'], result=result, refreshid=refreshid).replace('<<', '{').replace('>>', '}'))  # '<!- infinite time=%s -->' % (int(time.time()))) + result + SafeText('<!- end infinite -->')
        else:
            from django.http import HttpResponse
            result = self.nodelist.render(context)
            context['view'].response = HttpResponse(result)
            return SafeText(result)


# rawhtml
@register.tag('rawhtml')
def do_rawhtml(parser, token):
    import django.template.base
    django.template.base.Parser
    endtag = 'endrawhtml'
    nodelist = parser.parse((endtag,))
    endblock = parser.next_token()
    acceptable_endblocks = (endtag,)
    if endblock.contents not in acceptable_endblocks:
        parser.invalid_block_tag(endblock, endtag, acceptable_endblocks)
    print endblock.contents
    print  nodelist
    return RawHtmlTag(nodelist)


class RawHtmlTag(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def __repr__(self):
        return "<Cache Node: %s. Contents: %r>" % (self.name, self.nodelist)

    def render(self, context):
        from django.utils.safestring import SafeText
        result = self.nodelist.render(context)
        return SafeText(result)


@register.filter
def getforeign(obj, name):
    '''对字符串进行键值对分割'''
    return getattr(obj, name.replace('_id', '')) if getattr(obj, name) else None

@register.filter
def getobjattr(obj, name):
    '''对字符串进行键值对分割'''
    return getattr(obj, name)

@register.filter
def getobjitem(obj, name):
    '''对字符串进行键值对分割'''
    return obj[name]

@register.filter
def multiply(v1, v2):
    return float(v1 or '0') * float(v2 or '0')

@register.filter('int')
def toint(v):
    return int(v or '0')

@register.filter
def parsekeyvals(s, seg=',', eq=':'):
    '''对字符串进行键值对分割'''
    import re
#     p = '([^:^,]+):([^:^,]*)'
    p = '([^{seg}^{eq}]+):([^{seg}^eq]*)'.format(seg=seg, eq=eq)
    return [{'key':r[0], 'val':r[1]} for r in re.findall(p, s)]

if __name__ == '__main__':
    print signfloat(0)
    print signfloat(5)
    print signfloat(-8)
