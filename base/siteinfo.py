# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-10-22

@author: Robin
'''
from models import CallMixin
from django.conf import settings
import datetime
import json, time, os
from django.utils.functional import cached_property
from defs import MessageChannel as MC
import logging, time
RAW_OPERATIONS = [

                 ]

class Site(object, CallMixin):
    easyversion = u'-1.4.4'

    @property
    def staticversion(self):
        return self.setting.get('staticversion') or str(int(time.time() / 60))
    
    @property
    def siteurl(self):
        return self.setting.get('siteurl').strip('/')
    
    @property
    def title(self):
        return self.setting.get('title')

    @property
    def timestamp(self):
        return int(time.time())

    @property
    def sys_debug(self):
        return self.setting.get('sys_debug')
    
    SITE_CACHEKEY = 'site_cachekey'
    _cachekeytime = 0
    _cachekey = None
    @property
    def cachekey(self):
        if not self._cachekey or (time.time() - self._cachekeytime) > 60:
            # 需更新Cache
            print 'ref site_cachekey'
            from base.utils import get_or_set_cache
            def get():
                return int(time.time())
            self._cachekey = get_or_set_cache(Site.SITE_CACHEKEY, get, timeout=60 * 60 * 24)
            self._cachekeytime = time.time()
        return self._cachekey

    _setting = None
    _setttingkey = None
    @property
    def setting(self):
        # 设置
        from models import KeyValue
        if not self._setting or self._setttingkey != self.cachekey:
            print 'load setting'
            self._setttingkey = self.cachekey
            self._setting = KeyValue.gen_setting([
                                        ('title', 'text', u'网站标题', '网站标题', None),
                                        ('hotline', 'text', u'热线电话', '4006701001', None),
                                        ('copyright', 'text', u'版权', '云南银软科技有限公司', None),
                                        ('techsupport', 'text', u'技术支持', '云南银软科技有限公司', None),
                                        ('techsupportsite', 'text', u'技术支持地址', 'http://www.inruan.com/', None),

                                        ('sys_debug', 'bool', u'系统调试', 'true', None),
                                        ('staticversion', 'text', u'静态资源版本', '', None),
            ], ckord=True, autodel=True)
        return self._setting
    

    @property
    def today(self):
        from utils import parsedate
        return parsedate(self.setting.get('sitedate')) or datetime.date.today()

    # 操作权限
    raw_operations = RAW_OPERATIONS
    _operations = None
    @property
    def operations(self):
        if not self._operations:
            self._operations = [
                                {
                                 'op':o[0].lower(),
                                 'name':o[1]
                                 }
                                
                                if o else None
                                
                                for o in self.raw_operations
                                ]
        return self._operations
    
    _alloperations = None
    @property
    def alloperations(self):
        if not self._alloperations:
            self._alloperations = set([v['op'] for v in self.operations if v])
        return self._alloperations
    
    _operationsmap = None
    @property
    def operationsmap(self):
        if not self._operationsmap:
            self._operationsmap = dict([(op[0].lower(), op[1]) for op in self.raw_operations if op and op[0]])
        return self._operationsmap
    
    @property
    def privileges(self):
        return dict([(k, ['admin'] + v.split(',')) for k, v in Site.raw_privileges.items() if v])
    
    @property
    def privileges_json(self):
        return json.dumps(self.privileges)
    
    # end 操作权限
    
    
    updatelogpath = os.path.join(settings.BASE_DIR, 'docs', 'updatelog.md')
    @property
    def updatelog(self):
        if os.path.exists(self.updatelogpath):
            return open(self.updatelogpath).read()
        else:
            return ''

    _lastupdatetime = None
    @property
    def lastupdatetime(self):
        if os.path.exists(self.updatelogpath) and not self._lastupdatetime or True:
            self._lastupdatetime = str(int(os.stat(os.path.join(settings.BASE_DIR, 'docs', 'updatelog.md')).st_mtime))
        else:
            self._lastupdatetime = 1  
        return self._lastupdatetime

    @property
    def roles(self):
        from xadmin.models import XRole
        return XRole.objects.filter()

    @property
    def xusers(self):
        from xadmin.models import XUser
        return XUser.objects.filter(status=XUser.STATUS_NORMAL)
    
    template_engines = {}
    
    # 七牛
    _qiniuinstance = None
    @property
    def qiniuenable(self):
        '''启用七牛云存储'''
        return self.setting['qiniu_enable']

    @property
    def qiniuinstance(self):
        '''七牛实例'''
        if not self.qiniuenable:
            raise Exception('未启用七牛云存储!')
        if not Site._qiniuinstance:
            from qiniu import Auth
            Site._qiniuinstance = Auth(access_key=self.setting['qiniu_access_key'], secret_key=self.setting['qiniu_secret_key'])
        return Site._qiniuinstance

    @property
    def qiniuuploadtoken(self):
        '''七牛上传凭证'''
        return self.gen_qiniuuploadtoken()

    def gen_qiniuuploadtoken(self, key=None):
        '''生成七牛上传凭证'''
        return self.qiniuinstance.upload_token(bucket=self.setting['qiniu_bucket'], key=key, policy={
            'returnBody':json.dumps([{'url': self.qiniubaseurl + '${key}', 'filename':'${fname}', 'name':'${fname}', 'size':'${fsize}'}]),
            'saveKey':self.setting.get('qiniu_prefix') + '/${year}${mon}${day}/${etag}${ext}'
        })

    @property
    def qiniubaseurl(self):
        '''七牛空间根地址'''
        return self.setting['qiniu_baseurl']
    
    # End 七牛

    # 单例
    _site = None
    @classmethod
    def reset_site(cls):
        from base.utils import del_cache
        del_cache(Site.SITE_CACHEKEY)
        Site._site = None
    
    @classmethod
    def get_site(cls):
        if Site._site == None:
            Site._site = Site()
            print 'new site', id(Site._site) 
        return Site._site
    # End 单例
    
    # 数据字典
    datadics = [
                ('color', u'颜色'),
                ('level', u'等级'),
                ('norm', u'包装规格'),
                ('length', u'指条长度'),
                ('maturity', u'花苞成熟度'),
                ('flaw', u'瑕疵说明'),
                ('feature', u'优点'),
                ('unit', u'单位'),
                ('evaluation', u'快捷评价'),
                ('logisticstype', u'物流类型'),
                ('frequency', u'班次'),
                ('banktype', u'发卡银行'),
                # ('logisticstypetype', u'物流类型'),
                
                ('shopattribute', u'商店商品属性'),
                ('shoplogisticstype', u'商店物流类型'),
                ]

    # 新闻
    _PageNews = None
    @property
    def page(self):
        '''单页面'''
        if not self._PageNews:
            class SN(object):
                def __getattr__(self, name):
                    from base.utils import get_or_set_cache
                    from news.models import News
                    return get_or_set_cache('site_pagenews_%s' % name, News.objects.filter(tag=name).first)
            self._PageNews = SN()
        return self._PageNews
    
    @property
    def newslist(self):
        '''新闻列表'''
        from news.models import News
        return News.objects.filter(tag='news')
    
    @property
    def noticelist(self):
        '''公告列表'''
        from news.models import News
        return News.objects.filter(tag='notice')
    
    def get_news_by_tag(self, tag):
        '''根据类型获取新闻列表'''
        from news.models import News
        return News.objects.filter(tag=tag)
    
    @property
    def products(self):
        '''商品列表'''
        from main.models import Product
        return Product.objects.filter(status=Product.STATUS_SALING)
    
    @property
    def promoteproducts(self):
        '''特价商品列表'''
        from main.models import Product, ProductTag
        tag = 'promote'
        # pquery = self.products.filter(id__in=ProductTag.objects.filter(tag=tag, product__status=Product.STATUS_SALING, flag=True).values_list('product_id', flat=True))
        pquery = self.products.order_by('pproduct__ordering')
        return pquery
    
    # 系统状态
    STATUS_NORMAL = 0  # 未开盘
    STATUS_OPENING = 10  # 开盘中
    STATUS_CLOSING = 100  # 收盘中（如正在计算订单）
    STATUS_CLOSED = 1000  # 已收盘, (场次才有该属性)
    STATUS_CANCELED = -1  # 已收盘, (场次才有该属性)
#     status = STATUS_NORMAL
    
    @property
    def status(self):
        return self.trade and self.trade.status or Site.STATUS_NORMAL
    
    @property
    def is_normal(self):
        return self.status == Site.STATUS_NORMAL

    @property
    def is_opening(self):
        return self.status == Site.STATUS_OPENING
    
    @property
    def buyable(self):
        return self.setting.get('buyablealways') or self.is_opening
    
    @property
    def trade(self):
        '''当前交易场次'''
        from main.models import Trade
        from django.db.models import Q
        trade = Trade.objects.filter(Q(status__in=[Site.STATUS_CLOSING, Site.STATUS_OPENING]) | Q(end__gte=datetime.datetime.now())).exclude(status=Site.STATUS_CANCELED).order_by('start').first()
        return trade        
    
    def timeticks(self):
        from main.models import Trade
        logger = logging.getLogger('django.info')
        trade = self.trade
        timestamp = time.time()
        logger.info('ticks t1 %s' % timestamp)
        print 't1', time.time()
        if not trade or trade.status == Site.STATUS_CLOSED or trade.status == Site.STATUS_CANCELED:
            # 最后一场已经结束
            logger.info('ticks f1 %s' % timestamp)
            # 查看是否需要自动创建交易场次
            from base.utils import parse_time
            today = datetime.date.today()
            before = 60 * 30  # 开始前多长时间自动创建
            todaystamp = time.mktime(today.timetuple())
            nowstamp = time.mktime(datetime.datetime.now().timetuple())
            for sg in self.setting.get('openingtimesegs'):
                start = parse_time(sg.get('start'))
                end = parse_time(sg.get('end'))
                name = sg.get('name') or u'未命名'
                if start == None or end == None:
                    continue
                if end <= start:
                    end += 60 * 60 * 24
                startstamp = todaystamp + start
                endstamp = todaystamp + end
                beforestamp = startstamp - before
                if nowstamp < beforestamp or nowstamp > endstamp:
                    continue
                
                # 创建交易场次
                trade = Trade(start=datetime.datetime.fromtimestamp(startstamp), end=datetime.datetime.fromtimestamp(endstamp))
                trade.offsetday = sg.get('offsetday') or 0
                trade.allarea = sg.get('allarea')
                trade.allowcities = sg.get('allowcities')
                trade.denycities = sg.get('denycities')
                trade.groupable = self.setting.get('groupable')
                trade.bidable = self.setting.get('bidable')
                trade.tradetype = sg.get('tradetype') or 0
                trade.date = trade.start
                trade.name = trade.date.strftime(name)
                trade.save()
                break
        elif trade and trade.status == Site.STATUS_OPENING:
            # 正在开盘中
            logger.info('ticks f2 %s' % timestamp)
            nowdt = datetime.datetime.now()
            if nowdt > trade.end:
                # 已经该结束了
                self.closetrade(trade.id)
        elif trade and trade.status == Site.STATUS_NORMAL:
            # 自动更新状态
            logger.info('ticks f3 %s' % timestamp)
            oldstatus = trade.status
            trade.calc_status()
            if oldstatus != trade.status:
                trade.save()
        logger.info('ticks t2 %s' % timestamp)
        print 't2', time.time()
#         self.doTaskTicks()
        logger.info('ticks t3 %s' % timestamp)
        print 't3', time.time()
        self.doOrderTicks()
        logger.info('ticks t4 %s' % timestamp)
        print 't4', time.time()
#         self.doClearTicks()
        self.doAutoSettleTask()
        logger.info('ticks t5 %s' % timestamp)
        print 't5', time.time()
        self.doAppPayNotify()
        logger.info('ticks t6 %s' % timestamp)
        print 't6', time.time()
        if self.setting.get('agencyable') and trade and not trade.agencyhandled:
            logger.info('ticks af1 %s' % timestamp)
            from agency.models import AgencyOrder
            from agency.utils import createOrderByAgencyOrder
            self.doAutoCancelAgencyOrder()
            self.doAutoReceiveAgencyOrder()
            logger.info('ticks af2 %s' % timestamp)
            ett = self.setting.get('early_termination_time')
            endtime = trade.end - datetime.timedelta(minutes=ett)
            if datetime.datetime.now() > endtime:
                trade.agencyhandled = datetime.datetime.now()
                trade.save(update_fields=['agencyhandled'])
                
                # 在平台下单
                logger.info('ticks af1-1 %s' % timestamp)
                createOrderByAgencyOrder()
                logger.info('ticks af1-2 %s' % timestamp)
                # 取消其他订单
                for ao in AgencyOrder.objects.filter(trade=trade, handled__isnull=True, status=AgencyOrder.STATUS_CONFIRMED):
                    ao.cancel(reason=u'场次结束平台自动取消')
        # 商店任务
        if self.setting.get('shopenable'):
            self.doAutoCancelShopOrder()
            self.doAutoReceiveShopOrder()

        logger.info('ticks exit %s' % timestamp)
        
    def closetrade(self, trade_id):
        '''结束交易'''
        # 计算团购、竞价等订单
        # 下面的操作需要数据库事务支持
        from main.models import Trade, Order, OrderItem, ItemType
        from django.db import transaction
        with transaction.atomic():
            trade = Trade.objects.filter(pk=trade_id).first()
            # 取消无关订单
            for order in Order.objects.exclude(trade=trade).filter(status=Order.STATUS_UNCONFIRM):
                order.cancel(u'已失效，系统自动取消')
            
            # 确认团购
            pdic = {}
            oquery = Order.objects.filter(trade=trade).filter(status=Order.STATUS_UNCONFIRM)
            oids = [r[0] for r in oquery.values_list('id')]
            if oids:
                uids = []
                for oi in OrderItem.objects.filter(order_id__in=oids, itemtype=ItemType.TYPE_GROUP).select_related('product'):
                    # 找出团购项
                    if not oi.product.groupable or not trade.groupable:
                        # 不能团购
                        oi.product.doSale(-1 * oi.quantity)
                        oi.reason = u'不能团购'
                        oi.quantity = 0
                        oi.calculate()
                        oi.save()
                        continue
                    if oi.product_id not in pdic:
                        pdic[oi.product_id] = {
                                               'quantity':0,
                                               'product':oi.product,
                                               'orderitems':[]
                                               }
                    pd = pdic[oi.product_id]
                    pd['quantity'] += oi.quantity
                    pd['orderitems'].append(oi)
                for pd in pdic.values():
                    product = pd['product']
                    group = product.group
                    price = product.price
                    dirate = 100  # 不打折, 100%
                    quantity = pd['quantity']
                    group.sort(key=lambda x:x['amount'], reverse=True)
                    for g in group:
                        if g['amount'] != '' and quantity >= int(g['amount']):
                            dirate = g['price']
                    dirate = int(dirate)
                    if dirate < 100:
                        # 享受折扣
                        price = price * dirate / 100
                        for oi in pd['orderitems']:
                            oi.price = price
                            oi.calculate()
                            oi.save()
                # END团购确认
                
                # 竞价确认
                pdic = {}
                for oi in OrderItem.objects.filter(order_id__in=oids, itemtype=ItemType.TYPE_BID).select_related('product'):
                    # 找出竞价项目
                    if not oi.product.bidable or not trade.bidable:
                        # 不能竞价
                        oi.reason = u'不能竞价'
                        oi.quantity = 0
                        oi.calculate()
                        oi.save()
                        continue
                    if oi.product_id not in pdic:
                        pdic[oi.product_id] = {
                                               'product':oi.product,
                                               'orderitems':[]
                                               }
                    pd = pdic[oi.product_id]
                    pd['orderitems'].append(oi)
                for pd in pdic.values():
                    product = pd['product']
                    price = product.price
                    minprice = product.minprice  # 底价
                    quantity = 0
                    
                    orderitems = pd['orderitems']
                    orderitems.sort(key=lambda oi:oi.price, reverse=True)
                    for oi in orderitems:
                        if oi.price >= minprice and quantity <= product.stock:
                            oi.quantity = min(product.stock - quantity, oi.quantity)
                            quantity += oi.quantity
                        else:
                            oi.reason = u'出价过低' if oi.price < minprice else u'商品无货'
                            oi.quantity = 0
                        oi.calculate()
                        oi.save()
                    if quantity:
                        product.doSale(quantity)
                # END竞价确认
                
                # 更新订单信息
                for order in oquery:
                    order.calculate()
                    order.status = Order.STATUS_CONFIRMED
                    order.save(update_fields=['count', 'quantity', 'totalprice', 'sellercomm', 'buyercomm', 'finalprice', 'status'])
                    if order.count == 0:
                        order.cancel(u'系统自动取消')
                    uids.append(order.buyer_id)
                if uids:
                    self.sendMessage(set(uids), u'%s确认完成' % trade.name, u'您好，%s的所有订单都已自动确认完成，请尽快前往商城查看。' % trade.name, '/me/order/', MC.WARN)
            
            trade.statu = Site.STATUS_CLOSED
            trade.save()
            
            try:
                # 处理商品
                from main.models import Product
                from django.db.models import F
                pquery = Product.objects.filter(status=Product.STATUS_SALING)
                if self.setting.get('autodownwhenclose') and self.setting.get('clearstockwhenclose'):
                    # 下架 清空库存
                    pquery.update(status=Product.STATUS_NORMAL, sales=0, stock=0, total=0)
                elif self.setting.get('autodownwhenclose'):
                    # 下架
                    pquery.update(status=Product.STATUS_NORMAL, sales=0, total=F('stock'))
                elif self.setting.get('clearstockwhenclose'):
                    # 清空库存
                    pquery.update(sales=0, stock=0, total=0)
                else:
                    pquery.update(sales=0, total=F('stock'))
                pquery.filter(stock=0).update(status=Product.STATUS_NORMAL)
            except Exception, e:
                print e

            if self.setting.get('clearcartwhenclose'):
                from main.models import CartItem
                CartItem.objects.filter().delete()
    @property
    def daysign_key(self):
        fmt = self.setting.get('daysign_key_format')
        return datetime.datetime.now().strftime(fmt) if fmt else None

    @property
    def prompt_key(self):
        fmt = self.setting.get('prompt_key_format')
        return datetime.datetime.now().strftime(fmt) if fmt else None
    
    def addTask(self, tag, data, priority=0):
        '''添加任务队列'''
        if self.setting.get('taskqueueable'):
            from task.models import Task
            t = Task(tag=tag, data=data, priority=priority)
            t.save()
            return t
        else:
            return self.doTask(tag, data)
        
    def getTask(self, tag=None):
        '''获取未执行的'''
        from task.models import Task
        query = Task.objects.filter(status=Task.STATUS_WAITTING).order_by('-priority', 'ordering', 'id')
        if tag:
            query = query.filter(tag=tag)
        return query.first()
    
    def doTask(self, tag, data):
        if tag == 'sendmessage':
            param = {
                    k:data[k]
                    for k in ['receiveids', 'title', 'content', 'link', 'json', 'senderid', 'level', 'channel'] if k in data
                }
            self.doSendMessage(**param)
    
    def doClearTicks(self):
        '''清算交易场次'''
        import re
        from main.models import Trade, Order
        tquery = Trade.objects.filter(cleared=None)
        rs = re.findall('(\d+):(\d+)', self.setting.get('tradecleartime'))
        if rs:
            rs = rs[0]
        now = datetime.datetime.now()
        if rs and int(rs[0]) == now.hour and int(rs[1]) == now.minute and tquery.count():
            from django.db import transaction
            with transaction.atomic():
                for trade in tquery:
                    trade.calc_status()
                    for o in trade.orders.exclude(sent=None).filter(received=None, status=Order.STATUS_CONFIRMED):
                        o.received = now
                        o.paydeadline = o.received + datetime.timedelta(days=o.depositday, hours=0 if o.depositday else 1)
                        o.save(update_fields=['received', 'paydeadline'])
                        o.check_finished()
                        self.sendMessage(o.seller_id, title=u'自动确认通知', content=u'订单%s已由系统自动确认收货。' % (o.ordernum), link='/sup/order/%s' % o.id)
                        self.sendMessage(o.buyer_id, title=u'自动确认通知', content=u'订单%s已由系统自动确认收货。' % (o.ordernum), link='/me/order/%s' % o.id)
                    trade.cleared = now
                    trade.save()
        
    def doOrderTicks(self):
        '''订单任务'''
        from main.models import Order
        from decimal import Decimal
        # 逾期惩罚
        fmt = self.setting.get('punishment_key_format')
        key = datetime.datetime.now().strftime(fmt) if fmt else None
        factor = self.setting.get('punishmentfactor').strip()
        punishv = float(factor.strip('%') or '0')
        if punishv:
            isperm = factor.endswith('%')
            for o in Order.objects.exclude(status=Order.STATUS_CANCELED).filter(finalpaid=None, paydeadline__lte=datetime.datetime.now()).select_related('buyer'):
                print 'o', o.id, time.time()
                data = o.json
                if type(data) != dict:
                    data = {}
                pd = data.get('punishment') or {}
                ps = pd.get(key)
                if not ps:
                    print 'o ps', o.id, time.time()
                    # 需要惩罚
                    if isperm:
                        pv = int(punishv * 10) * o.finalprice / 1000
                    else:
                        pv = Decimal(punishv)
                    
                    pd[key] = {
                               'datetime':datetime.datetime.now(),
                               'value':pv
                               }
                    o.buyer.changeValues(u'订单%s货款逾期惩罚' % o.ordernum, transaction=True, value_credit=-1 * pv, model='Order', objid=u'%s' % o.id)
                    self.sendMessage(o.buyer_id, u'货款逾期惩罚', u'你好，因为你的订单%s未在承诺时间段内未支付货款，因此平台降低了你的授信额度，请保持良好的信用记录' % o.ordernum, link='/me/order/%d' % o.id)
                    data['punishment'] = pd
                    o.json = data
                    o.save(update_fields=['json'])
            
    
    def doTaskTicks(self):
        '''任务周期'''
        from task.models import Task
        maxtime = 2  # 最多执行这么长时间, 0不限制
        maxcount = 30  # 最多执行这么多任务, 0不限制
        count = 0
        start = time.time()
        while (maxcount == 0 or count < maxcount) and (maxtime == 0 or (time.time() - start) < maxtime):
            t = self.getTask()
            if not t:
                break
            t.status = Task.STATUS_DOING
            t.done = datetime.datetime.now()
            t.save(update_fields=['status', 'done'])
            
            data = t.data
            tag = t.tag
            try:
                self.doTask(tag, data)
                t.status = Task.STATUS_SUCCESS 
            except Exception, e:
                print e
                t.status = Task.STATUS_FAILED
            t.done = datetime.datetime.now()
            t.save(update_fields=['status', 'done'])
            count += 1
        return count
    
    def doAutoSettleTask(self):
        '''自动确认'''
        import re
        now = datetime.datetime.now()
        
        autosettletime_hours = self.setting.get('autosettletime_hours')
        count = 0
        rs = re.findall('(\d+):(\d+)', self.setting.get('tradecleartime'))
        if rs:
            rs = rs[0]
        clearable = rs and int(rs[0]) == now.hour and int(rs[1]) == now.minute
        if autosettletime_hours and autosettletime_hours > 0:
            from main.models import BigOrder
            from django.db.models import Q
            
            limitdt = now - datetime.timedelta(hours=autosettletime_hours)
#             limitdt = now - datetime.timedelta(seconds=1)
            localids = self.localcity.get_subidarray() + [self.localcity.id]
            bigq = BigOrder.objects.filter(Q(xdelivered__lte=limitdt) | Q(area_id__in=localids)).filter(status=BigOrder.STATUS_UNFINISH)
            if bigq.count():
                # 有需要处理的大订单
                from django.db import transaction
                supids = set()
                with transaction.atomic():
                    for bo in bigq:
                        print bo.bigordernum
                        if bo.orders.count() == 0:
                            # 没有有效的订单，自动取消大订单
                            bo.status = BigOrder.STATUS_CANCELED
                            bo.save(update_fields=['status'])
                            continue
                        if bo.orders.filter(sent__isnull=True).count():
                            # 还有订单没有发货
                            continue
                        if (bo.area_id not in localids and bo.xdelivered) or (bo.area_id in localids and clearable):
                            for o in bo.orders.filter(received__isnull=True):
                                # 每个订单自动收货
                                o.received = now
                                o.paydeadline = o.received + datetime.timedelta(days=o.depositday, hours=0 if o.depositday else 1)
                                o.save(update_fields=['received', 'paydeadline'])
                                o.check_finished(checkbig=False)
                                if o.supplier_id:
                                    supids.add(o.supplier_id)
                                self.sendMessage(o.seller_id, title=u'自动确认通知', content=u'订单%s已由系统自动确认收货。' % (o.ordernum), link='/sup/order/%s' % o.id)
#                                 self.sendMessage(o.buyer_id, title=u'自动确认通知', content=u'订单%s已由系统自动确认收货。' % (o.ordernum), link='/me/order/%s' % o.id)
                        nbo = BigOrder.objects.filter(id=bo.id).first()
                        nbo.check_finished()
                if supids:
                    # 有供货商排名信息需要更新
                    from supplier.models import Supplier
                    for sup in Supplier.objects.filter(id__in=set(supids)):
                        sup.refresh_rank()
#             BigOrder.objects.filter()
        return count

    def doAutoCancelAgencyOrder(self):
        '''自动取消未支付的合伙人订单'''
        if self.setting.get('autoCancelAgencyOrders_time'):
            from agency.models import AgencyOrder
            # 过期时间
            now = datetime.datetime.now()
            gtime = now - datetime.timedelta(minutes=self.setting.get('autoCancelAgencyOrders_time'))
            aoquery = AgencyOrder.objects.filter(finalpaid=None, created__lte=gtime).exclude(status=AgencyOrder.STATUS_CANCELED)
#             print aoquery
            if not aoquery.count():
                # 没有需要自动取消的订单
                return
            for a in aoquery:
                a.cancel(reason=u'支付超时平台自动取消')

    def doAutoReceiveAgencyOrder(self):
        '''自动收货分销商订单'''
        if self.setting.get('autoReceiveAgencyOrders_time'):
            from agency.models import AgencyOrder
            now = datetime.datetime.now()
            gtime = now - datetime.timedelta(hours=self.setting.get('autoReceiveAgencyOrders_time'))
            aoquery = AgencyOrder.objects.filter(finalpaid__isnull=False, sent__isnull=False, received=None, sent__lte=gtime).exclude(status=AgencyOrder.STATUS_CANCELED).select_related('agency')
            if not aoquery.count():
                # 没有需要自动收货的订单
                return
            for i in aoquery:
                i.received = now
                i.save(update_fields=['received'])
                from django.db import transaction as dbtransaction
                with dbtransaction.atomic():
                    i.check_finished()
                self.sendMessage(i.agency.owner_id, title=u'验收通知', content=u'订单%s已由系统自动收货。' % (i.ordernum))

    def doAutoCancelShopOrder(self):
        '''自动取消未支付的商店订单'''
        if self.setting.get('autoCancelShopOrders_time'):
            from shop.models import ShopOrder
            # 过期时间
            now = datetime.datetime.now()
            gtime = now - datetime.timedelta(minutes=self.setting.get('autoCancelShopOrders_time'))
            soquery = ShopOrder.objects.filter(finalpaid=None, created__lte=gtime).exclude(
                status=ShopOrder.STATUS_CANCELED)
            #             print aoquery
            if not soquery.count():
                # 没有需要自动取消的订单
                return
            for a in soquery:
                a.cancel(reason=u'支付超时平台自动取消')

    def doAutoReceiveShopOrder(self):
        '''自动收货商店订单'''
        if self.setting.get('autoReceiveShopOrders_time'):
            from shop.models import ShopOrder
            now = datetime.datetime.now()
            gtime = now - datetime.timedelta(hours=self.setting.get('autoReceiveShopOrders_time'))
            soquery = ShopOrder.objects.filter(finalpaid__isnull=False, sent__isnull=False, received=None, sent__lte=gtime).exclude(status=ShopOrder.STATUS_CANCELED).select_related('shopseller')
            if not soquery.count():
                # 没有需要自动收货的订单
                return
            for i in soquery:
                if i.aftersales and i.aftersales.is_unhandle:
                    continue
                i.received = now
                i.save(update_fields=['received'])
                from django.db import transaction as dbtransaction
                with dbtransaction.atomic():
                    i.check_finished()
                self.sendMessage(i.shopseller.owner_id, title=u'验收通知', content=u'订单%s已由系统自动收货。' % (i.ordernum))
    
    def sendMessage(self, receiveids, title, content, link=None, json=None, senderid=0, channel=MC.NORMAL):
        '''发送消息'''
        if receiveids and type(receiveids) not in [list, set, tuple]:
            receiveids = [receiveids]
        self.addTask(tag='sendmessage', data={
                'receiveids':list(receiveids),
                'title':title,
                'content':content,
                'link':link,
                'json':json,
                'senderid':senderid,
                'channel':channel
            })
    
    def doSendMessage(self, receiveids, title, content, link=None, json=None, senderid=0, channel=MC.NORMAL):
        '''直接发送消息'''
        # 普通站内消息
        from user.models import User
        from message.models import Message
        import traceback
        if not self.setting.get('sendmessageable'):
            return None
        if receiveids and type(receiveids) not in [list, set, tuple]:
            receiveids = [receiveids]
        
        # 站内消息
        try:
            msgs = []
            if receiveids:
                for rid in receiveids:
                    msg = Message(receiver_id=rid, title=title, content=content, link=link, json=json)
                    if senderid:
                        msg.sender_id = senderid
                    msgs.append(msg)
            else:
                # 群发
                msg = Message(receiver=None, title=title, content=content, link=link, json=json)
                msgs.append(msg)
            if msgs:
                Message.objects.bulk_create(msgs)
        except:
            pass
        
        if not receiveids:
            return
        users = [u for u in User.objects.filter(id__in=receiveids)]
        
        # 使用微信发送消息
        try:
            if channel & MC.WX and self.setting.get('wx_enable') and self.setting.get('wx_notifyenable'):
                wechat_instance = self.wechat_instance
                wxcontent = content
                if link:
                    wxlink = link
                    if '://' not in link:
                        wxlink = u'%s%s' % (self.siteurl, link)
                    wxcontent = u'%s 详情:%s' % (content, wxlink)
                if wechat_instance:
                    for u in users:
                        if not u.openid:
                            continue
                        data = u.json
                        if type(data) != dict:
                            data = {}
                        userid = data.get('wx_userid')
                        if not userid:
                            openid = u.openid
                            try:
                                res = wechat_instance.corp_convert_to_userid(openid)
                                if res.get('userid'):
                                    userid = res.get('userid')
                                    data['wx_userid'] = userid
                                    u.json = data
                                    u.save(update_fields=['json'])
                            except Exception, e:
                                traceback.print_exc()
                                print 'Trans OpenId Err:', e
                        if userid:
                            wechat_instance.corp_send_text_message(userid, wxcontent, self.wxsetting['msg_agentid'])
        except Exception, e:
            traceback.print_exc()
            print 'Send WX Msg Err:', e
        
        # APP
        if channel & MC.PUSH and self.setting.get('umpush_enable'):
            from third import umpush
            client = umpush.UMMsgClient(appKey=self.setting.get('umpush_appkey'), appMasterSecret=self.setting.get('umpush_mastersecret'))
            try:
                pslink = link
                if link and '://' not in link:
                    pslink = u'%s%s' % (self.siteurl, link)
                client.sendNotify(title, content, link=pslink, alias=','.join([u.username for u in users]))
            except Exception, e:
                traceback.print_exc()
                print 'APP Push Err:', e
        
        # 短信
        if channel & MC.SMS and self.setting.get('usersmsnoticeable'):
            # 短信通知
            phones = []
            for u in users:
                if not u.phone:
                    continue
                phones.append(u.phone)
            if phones:
                smscontent = title
                try:
                    # 短信有可能发送失败
                    self.sendPhoneNotice(','.join(phones), '', smscontent)
                except Exception, e:
                    traceback.print_exc()
                    print 'SMS Err:', len(smscontent), e
        
        
        return len(receiveids)
    
    _doAppPayNotifyPreTime = 0
    def doAppPayNotify(self):
        '''对外支付通知'''
        import threading, requests
        from external.models import AppPay
        if time.time() - self._doAppPayNotifyPreTime < 60:
            return
        self._doAppPayNotifyPreTime = time.time()
        now = datetime.datetime.now()
        checkafter = now + datetime.timedelta(minutes=-5)  # 只通知5分钟内的
        def doit():
            aquery = AppPay.objects.filter().exclude(notifyurl="").filter(paydatetime__gte=checkafter, notifytime__isnull=True).order_by('updated')
            for ap in aquery[0:10]:
                if ap.notifyurl:
                    try:
                        print 'notify', ap.notifyurl
                        res = requests.get(ap.notifyurl).text
                        print res
                        if 'OK' in res.upper():
                            ap.notifytime = datetime.datetime.now()
                            ap.save(update_fields=['notifytime'])
                    except Exception, e:
                        print 'notify error', e
                        pass
            time.sleep(2)
            self._doAppPayNotifyPreTime = 0
        threading.Thread(target=doit).start()
        
    @property
    def classifies(self):
        '''顶层分类'''
        from preset.models import Classify
        return Classify.objects.filter(parent=None)
    
    @property
    def pproducts(self):
        '''商品库列表'''
        from preset.models import PProduct
        return PProduct.objects.filter()
    
    def get_modellist(self, modelname):
        '''获取模型对象列表'''
        from xadmin.views import AdminView
        m = AdminView().get_model(modelname)
        if m:
            return m.objects.filter()
        else:
            raise Exception('找不到模型:%s' % modelname)


    def get_template_engines(self, lang=None):
        templpath = settings.TEMPLATE_BASE_DIR
        if not lang:
            lang = settings.MAIN_LANG
        if lang != settings.MAIN_LANG:
            lang_templpath = os.path.join(settings.TEMPLATE_BASE_DIR, 'locals', lang)  # os.path.join(settings.TEMPLATE_BASE_DIR, 'locals', lang, templ)
            if not os.path.exists(lang_templpath):
                self.lang = lang = settings.MAIN_LANG
                print u'lang templpath not exists: %s' % lang_templpath
            else:
                templpath = lang_templpath
                
        from django.conf import settings as gsettings
        from django.template.backends.django import DjangoTemplates
        if templpath not in self.template_engines:
            self.template_engines[templpath] = DjangoTemplates({
              'APP_DIRS':False,
              'DIRS':[templpath],
              'NAME':'django',
              'OPTIONS':{
                    'allowed_include_roots': gsettings.ALLOWED_INCLUDE_ROOTS,
                    'context_processors': gsettings.TEMPLATE_CONTEXT_PROCESSORS,
                    'debug': gsettings.TEMPLATE_DEBUG,
                    'loaders': gsettings.TEMPLATE_LOADERS,
                    'string_if_invalid': gsettings.TEMPLATE_STRING_IF_INVALID,
                }
              })
        ng = self.template_engines[templpath]
        return ng

    # 微信公众号
    _wxsetting = None
    @property
    def wxsetting(self):
        if self.setting.get('wx_enable') and not self._wxsetting:
            self._wxsetting = {
                'appid':self.setting.get('wx_appid') if self.setting.get('wx_enable') else None,
                'appsecret': self.setting.get('wx_appsecret'),
                
                'token':self.setting.get('wx_msg_token'),
                'encoding_aes_key':self.setting.get('wx_msg_aeskey'),
                
                'msg_agentid':self.setting.get('wx_notify_appid')  if self.setting.get('wx_notifyenable')else None,
                
                'authcallback':'%s/wx/authcallback?_=%s' % (self.siteurl, time.time()),
            }
        return self._wxsetting
    
    _wechat_instance = None
    
    @property
    def wechat_instance(self):
        if not self._wechat_instance and self.wxsetting:
            from wechat.wxcorp import WechatCorp, CorpConf
            self._wechat_instance = WechatCorp(conf=CorpConf(
                appid=self.wxsetting.get('appid'),
                token=self.wxsetting.get('token'),
                encoding_aes_key=self.wxsetting.get('encoding_aes_key'),
                appsecret=self.wxsetting.get('appsecret')
            ))
        return self._wechat_instance
    
    
    def get_wechat_jssdk_config(self, url):
        from third.wxutils import nonce_str, sha1sign
        from base.utils import get_or_set_cache
        nonceStr = nonce_str()
        timestamp = int(time.time())
        def gettk():
            return self.wechat_instance.get_jsapi_ticket()['jsapi_ticket']
#         url = 'http://%s%s' % (request.get_host(), request.get_full_path())
        wx = {
               'timestamp':str(timestamp),
               'noncestr':nonceStr,
               'jsapi_ticket':get_or_set_cache('wx_jsapi_ticket', gettk, timeout=3600),
               'url':url
              }
        wx['signature'] = sha1sign(wx)
        wx['nonceStr'] = wx['noncestr']
        wx['appId'] = self.wxsetting['appid']
        return wx
    
    # END微信公众号
    
    # 小程序
    @cached_property
    def wxa_instance(self):
        from wechat.wxwxa import WechatWxa
        return WechatWxa(appid=self.setting['wxa_appid'], appsecret=self.setting['wxa_appsecret'])
    
    wxa_instance_map = {}  # 小程序对象集合
    def get_wxa_setting(self, wxatag):
        '''获取对应的小程序配置'''
        # 配置字典，必须wxa结尾(支付回调限制)
        tagmap = {
            'wxa': '',  # 分销商小程序
            'sitewxa': 'site_'  # 平台小程序
        }
        if wxatag not in tagmap:
            return None
        prex = tagmap[wxatag]
        enk = '%swxa_enable' % prex
        if not self.setting.get(enk):
            return None
        return {
            'APPID':self.setting.get('%swxa_appid' % prex),
            'APPSECRET':self.setting.get('%swxa_appsecret' % prex),
            'PARTNERID':self.setting.get('%spay_wxa_pid' % prex),
            'PARTNERKEY':self.setting.get('%spay_wxa_key' % prex),
        }
    def get_wxa_instance(self, wxatag):
        '''获取指定的小程序实例'''
        if wxatag not in self.wxa_instance_map:
            from wechat.wxwxa import WechatWxa
            setting = self.get_wxa_setting(wxatag)
            self.wxa_instance_map[wxatag] = setting and WechatWxa(appid=setting['APPID'], appsecret=setting['APPSECRET']) or None
        return self.wxa_instance_map[wxatag]
        
    # END小程序
    
    # 短信
    def get_alidayu_req(self):
        from third import top
        req = top.api.AlibabaAliqinFcSmsNumSendRequest()
        appkey = self.setting.get('alidayu_appkey')
        secret = self.setting.get('alidayu_secret')
        req.set_app_info(top.appinfo(appkey, secret))
        req.format = 'json'
        req.extend = "123456"
        req.sms_type = "normal"
        req.sms_free_sign_name = self.setting.get('alidayu_sign')
        return req
    
    def start_alidayu_req(self, req):
        try:
            req.getResponse()
            pass
        except Exception, e:
            import re
            s = str(e)
            rs = re.findall('submsg=(\S+)', s)
            print s
            if rs:
                s = rs[0]
            raise Exception(s)
        return True

    def sendPhoneNotice(self, phone, name, msg):
        """发送短信消息"""
        if self.setting.get('aliyun_sms_enable'):
            self.sendPhoneNoticeNew(phone, name, msg)
        else:
            self.sendPhoneNoticeOld(phone, name, msg)

    def sendVerifyPhone(self, phone, usetype, code):
        """发送验证码"""
        if self.setting.get('aliyun_sms_enable'):
            return self.sendVerifyPhoneNew(phone, usetype, code)
        else:
            return self.sendVerifyPhoneOld(phone, usetype, code)


    # 旧版短信
    def sendPhoneNoticeOld(self, phone, name, msg):
        if not self.setting.get('alidayu_enable'):
            return True
        
        req = self.get_alidayu_req() 
        req.sms_param = json.dumps({
            'name':name,
            'msg':msg
        })
        req.rec_num = phone
        req.sms_template_code = self.setting.get('alidayu_notice_templ')
        if self.start_alidayu_req(req):
            return True

    def sendVerifyPhoneOld(self, phone, usetype, code):
        if not self.setting.get('alidayu_enable'):
            return True
        req = self.get_alidayu_req()
        req.sms_param = json.dumps({
            'product':self.setting.get('alidayu_product'),
            'code':code
        })
        req.rec_num = phone
        req.sms_template_code = self.setting.get('alidayu_verify_phone_templ')
        if not self.setting.get('alidayu_enable') or self.start_alidayu_req(req):
            return True
    # END旧版短信

    # 新版短信接口
    def sendPhoneNoticeNew(self, phone, name, msg):
        """发送短信消息"""
        if not self.setting.get('aliyun_sms_enable'):
            return True
        from third.aliyunsms import send_sms
        import uuid
        ACCESS_KEY_ID = self.setting.get('aliyun_sms_ACCESS_KEY_ID')
        ACCESS_KEY_SECRET = self.setting.get('aliyun_sms_ACCESS_KEY_SECRET')
        sign_name = self.setting.get('aliyun_sms_sign')
        template_code = self.setting.get('aliyun_sms_notice_templ')
        params = json.dumps({
            'name': name,
            'msg': msg
        })
        __business_id = uuid.uuid1()
        res = send_sms(ACCESS_KEY_ID, ACCESS_KEY_SECRET, __business_id, phone, sign_name, template_code, params)
        res = json.loads(res)
        # print res
        if not isinstance(res, dict):
            res = {}
        if res.get('Code') == 'OK':
            return True
        else:
            print res, type(res)


    def sendVerifyPhoneNew(self, phone, usetype, code):
        """发送短信验证码"""
        if not self.setting.get('aliyun_sms_enable'):
            return False
        from third.aliyunsms import send_sms
        import uuid
        ACCESS_KEY_ID = self.setting.get('aliyun_sms_ACCESS_KEY_ID')
        ACCESS_KEY_SECRET = self.setting.get('aliyun_sms_ACCESS_KEY_SECRET')
        sign_name = self.setting.get('aliyun_sms_sign')
        template_code = self.setting.get('aliyun_sms_verify_phone_templ')
        params = json.dumps({
            'code': code,
        })
        __business_id = uuid.uuid1()
        res = send_sms(ACCESS_KEY_ID, ACCESS_KEY_SECRET, __business_id, phone, sign_name, template_code, params)
        res = json.loads(res)
        # print res
        if not isinstance(res, dict):
            res = {}
        if res.get('Code') == 'OK':
            return True
        else:
            print res, type(res)


    # END新版短信

    
    def sendAdminNotice(self, msg, tag=None):
        import re
        phones = re.findall('([\+\d]+)', self.setting.get('adminphones')) if self.setting.get('adminnoticeable') else None
        if phones:
            self.sendPhoneNotice(','.join(phones), u'管理员', msg)
    # END短信
    
    def get_orderranks(self, modelname, fieldname=None, objfields='id_name'):
        from utils import splitstrip
        if not fieldname:
            fieldname = modelname
        objfields = splitstrip(objfields, '_')
        def get_orderranks():
            from main.models import Order
            from django.db.models import Sum, Count
            from utils import obj2dic
            from xadmin.views import AdminMixin
            query = Order.objects.filter().exclude(status=Order.STATUS_CANCELED)
            res = []
            order_by = '-sum_finalprice'
            query = query.order_by(order_by)
            if self.setting.get('rankdatetime'):
                query = query.filter(created__gte=self.setting.get('rankdatetime'))
            if self.setting.get('rankcount'):
                query = query[0:self.setting.get('rankcount')]
            fieldkey = '%s_id' % fieldname
            model = AdminMixin().get_model(modelname)
            for r in query.values(fieldkey).annotate(sum_count=Sum('count'), sum_quantity=Sum('quantity'), sum_finalprice=Sum('totalprice'), count=Count('id'),):
                obj = model.objects.filter(pk=r[fieldkey]).first() if r[fieldkey] else None
                r['obj'] = obj2dic(obj, objfields) if obj else None
                res.append(r)
            return res
        if self.setting.get('orderrankenable'):
            from base.utils import get_or_set_cache, md5
            vals = ''.join([str(r) for r in [modelname, fieldname, objfields, self.setting.get('orderrankenable'), self.setting.get('rankdatetime'), self.setting.get('rankcount'), self.setting.get('rankinterval')]])
            key = 'site_orderranks_%s' % (md5(vals))
            return get_or_set_cache(key, get_orderranks, timeout=self.setting.get('rankinterval'))
        else:
            return []

    
    def get_xrole(self, name):
        from xadmin.models import XRole
        return XRole.objects.filter(role=name).first()
    
    def get_xusers_by_role(self, name):
        from xadmin.models import XUser
        return XUser.objects.filter(role__role__icontains=name)
    
    @property
    def tradeable(self):
        return self.trade or self.setting.get('buyablealways')
    
    @property
    def groupable(self):
        trade = self.trade
        return trade and trade.groupable or self.setting.get('groupable')

    @property
    def bidable(self):
        trade = self.trade
        return trade and trade.bidable or self.setting.get('bidable')
    
    @property
    def ads(self):
        '''广告'''
        if self.setting.get('ad_count') >= 0:
            from news.models import Advertisement
            from django.db.models import Q
            query = Advertisement.objects.filter()
            now = datetime.datetime.now()
            query = query.filter((Q(starttime__lte=now) | Q(starttime__isnull=True)) and (Q(endtime__gte=now) | Q(endtime__isnull=True)))
            return query[0:self.setting.get('ad_count')] if self.setting.get('ad_count') else query
        else:
            return []
    
    def getAdsByKeyword(self, kw='', start=0, count=10):
        '''获取广告列表'''
        from base.utils import md5, get_or_set_cache
        key = u'site_%d_ads_%s' % (id(self), md5(u'kw=%s&start=%s&count=%s' % (kw, start, count)))
        def get():
            from news.models import Advertisement
            from django.db.models import Q
            query = Advertisement.objects.filter()
            now = datetime.datetime.now()
            query = query.filter((Q(starttime__lte=now) | Q(starttime__isnull=True)) and (Q(endtime__gte=now) | Q(endtime__isnull=True)))
            if kw:
                query = query.filter(keyword__icontains=kw)
            return [r for r in query[start:start + count]]
        return get_or_set_cache(key, get)
    
    @property
    def userlevels(self):
        from user.models import UserLevel
        return UserLevel.objects.filter()
    
    def doAutoUserLevel(self, begin=None, end=None, uids=None):
        '''执行用户自动分级'''
        from main.models import BigOrder
        from django.db.models import Sum
        from django.db.models.query import Q
        from user.models import UserLevel, User
        from base.utils import month_last_day
        if not self.setting.get('autouserlevel_months') and (not begin and not end):
            return []
        if not begin or not end:
            from dateutil.relativedelta import relativedelta
            today = self.today
            beginm = today + relativedelta(months=-1 * self.setting.get('autouserlevel_months'))
            begin = datetime.date(beginm.year, beginm.month, 1)  # today.strftime("%Y-%m-01")
            endm = today + relativedelta(months=-1)
            end = datetime.date(endm.year, endm.month, month_last_day(endm.year, endm.month))
#         print begin, end
        levels = [lv for lv in UserLevel.objects.filter(type=UserLevel.TYPE_AUTO).order_by('-target')]
        def getLevel(value):
            for lv in levels:
                if value >= lv.target:
                    return lv
            return None
        query = BigOrder.objects.filter(date__gte=begin, date__lte=end)
        sumfields = {
                     r:Sum(r)
                     for r in ['productfee', 'piecenum', 'transportfee', 'weight', 'littlefee', 'overweightfee', 'alltransportfee', \
                               'packagefee', 'otherfee', 'allotherfee', 'allfee', 'payment', 'settlement', 'buyercomm', 'presettlement']
                     }
        userIds = []
        for sm in query.values("buyer_id").annotate(**sumfields):
            lv = getLevel(sm['allfee'])
            us = User.objects.filter(id=sm['buyer_id']).select_related('level').first()
            if not us.level or us.level.type == UserLevel.TYPE_AUTO:
                # 自动分级
                us.level = lv
                us.save(update_fields=['level'])
                userIds.append(us.id)
        User.objects.exclude(id__in=userIds).filter(Q(level__isnull=True) | Q(level__type=UserLevel.TYPE_AUTO)).update(level=getLevel(0))
        return userIds
    
    _is_local = None
    @property
    def is_local(self):
        if self._is_local == None:
            import socket
            import re
            hostname = socket.gethostname()
            if not re.match('usa', hostname) and not re.match('sz', hostname) and not re.match('Cloud', hostname):
                self._is_local = True
            else:
                self._is_local = False
        return self._is_local

    @property
    def agency_trade_bool(self):
        """是否处在分销场次内"""
        import datetime
        trade = self.trade
        if not trade:
            return False
        if datetime.datetime.now() < trade.start:
            return False
        ett = self.setting.get('early_termination_time')
        # 处理订单，把场次结束提前3 分钟
        ett = max((ett + 3), 3)
        endtime = trade.end - datetime.timedelta(minutes=ett)
        if datetime.datetime.now() > endtime:
            return False
        return True

    @property
    def agency_buyable(self):
        """分销场次是否能交易"""
        return self.setting.get('buyablealways') or self.agency_trade_bool
    
    @property
    def ItemType(self):
        from main.models import ItemType
        return ItemType

    @property
    def shopAttrTemplateTypes(self):
        """商店商品属性类型"""
        return [{'name': r[1], 'type': r[0]} for r in [('radio', '单选'), ('multiple', '多选'), ('time', '时间'), ('text', '文本'), ('longtext', '长文本')]]

    @property
    def shopClassifies(self):
        from shop.models import ShopClassify
        return ShopClassify.objects.filter(level=1)
    
    @cached_property
    def cheme(self):
        '''网站协议'''
        url = self.siteurl or ''
        return 'https' if url.startswith('https://') else 'http'

    @cached_property
    def shop_top_classify(self):
        """商城顶级分类"""
        from shop.models import ShopClassify
        return ShopClassify.objects.filter(parent=None)

    @cached_property
    def irapi(self):
        from third.irapi import IRApi
        api = IRApi(appid=self.setting.get('irapi_appid'), appkey=self.setting.get('irapi_appkey'))
        return api

    @cached_property
    def site_get_agency(self):
        from agency.models import Agency
        return Agency.objects.filter(status=Agency.STATUS_NORMAL)

    @cached_property
    def shop_class_city(self):
        from preset.models import Area
        from base.utils import obj2dic
        return Area.objects.filter(level=0)

    @cached_property
    def supplier_flag_info(self):
        """供货商标记"""
        from supplier.models import get_flag_selections
        return get_flag_selections(v=True)

    @property
    def live_mall_productids(self):
        from base.utils import get_cache
        return get_cache('live_mall_productids') or []

    @live_mall_productids.setter
    def live_mall_productids(self, v):
        from base.utils import set_cache
        set_cache('live_mall_productids', v, timeout=60 * 60 * 24)

def get_site():
    return Site.get_site()

def get_setting(k):
    return Site.get_site().setting.get(k)
