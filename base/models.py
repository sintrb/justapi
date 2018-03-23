# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-10-22

@author: Robin
'''

from django.db import models
from base.fields import _
from base import fields as bfield
import json

class CallMixin:
    def __getattr__(self, name):
        '''
        方法注入
        '''
        if name.startswith("call__"):
              
            sps = name.split("__")
            fname = sps[1]
            try:
#                 print fname
                func = getattr(self, fname)
            except:
                raise Exception("get method failed: %s(%s)" % (name, fname))
            args = sps[2:]
            return func(*args)
        return getattr(super(BaseModel, self), name)  # super(BaseModel, self).__getattr__(name)
    pass

class StatusManager(models.Manager):
    STATUS_NORMAL = 0
    STATUS_CANCELED = -1
    STATUS_CHOICES = ((STATUS_NORMAL, "正常"), (STATUS_CANCELED, "已锁定"))
    STATUS_MAP = dict(STATUS_CHOICES)
    def filter(self, *args, **kwargs):
        return models.Manager.filter(self, *args, **kwargs).filter(status=StatusManager.STATUS_NORMAL)
    def exclude(self, *args, **kwargs):
        return models.Manager.exclude(self, *args, **kwargs).filter(status=StatusManager.STATUS_NORMAL)

class BaseModel(models.Model):
    ordering = models.IntegerField(_('排序权值'), default=0, db_index=True, editable=False)
    created = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated = models.DateTimeField(_('修改时间'), auto_now=True)
    class Meta:
        abstract = True
        ordering = ['-ordering', '-id']
        
    @classmethod
    def get_fields(clz):
        return clz._meta.fields
    
    @classmethod
    def get_allfields(clz):
        return [f.name for f in clz.get_fields()]

    @classmethod
    def get_editfields(clz):
        return [f.name for f in clz.get_fields() if f.editable and not f.primary_key]
    
    @classmethod
    def get_dictfields(cls, full=False):
        arr = []
        for f in cls.get_fields():
            if f.editable and not f.primary_key:
                fd = {
                     'name':f.name + "_id" if hasattr(f, 'rel') and hasattr(f.rel, 'to') else f.name,
                     'editable':f.editable and not f.primary_key,
                     'value':f.get_default(),
                     'type':f.__class__.__name__,
                     'max_length':f.max_length,
                     'required':not (f.blank or f.null),
                     'verbose_name':f.verbose_name,
                     'choices':f.choices,
                     'relmodel':(f.rel.to.__name__ if hasattr(f.rel.to, '__name__') else f.rel.to) if hasattr(f, 'rel') and hasattr(f.rel, 'to') else None
                     }
                if full:
                    fd['field'] = f
                arr.append(fd)
        return arr
    
    @classmethod
    def get_field(cls, name):
        rs = [f for f in cls.get_fields() if f.name == name]
        return rs[0] if rs else None
    
    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if not self.ordering:
            orderingby = getattr(self._meta, 'ordering', [])
            if orderingby and orderingby[0] == 'ordering':
                import time
                self.ordering = int(time.time())
        if self.id:
            from base.utils import del_cached_obj
            del_cached_obj(self)
        if update_fields:
            default_fields = ["updated"]
            update_fields = default_fields + update_fields
        return models.Model.save(self, force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)
    
    def to_json(self):
        return {
                'id':self.id
            }
    
class ChildrenModelMixin(object):
    autorefreshids = True
    
    @property
    def children(self):
        return self.get_children()
    
    @property
    def all_children(self):
        ids = self.get_subidarray()
        ids.remove(self.id)
        return type(self).objects.filter(pk__in=ids)
    
    def get_children(self, **filters):
        return type(self).objects.filter(parent_id=self.id, **filters).select_related('parent')
    
    @property
    def gap_children(self):
        return type(self).objects.filter(parent_id__in=[v[0] for v in type(self).objects.filter(parent_id=self.id).values_list('id')])
    
    def get_subidarray(self):
        subids = json.loads(self.subids)['v'] if type(self.subids) != type([]) else self.subids
        return subids
    
    def get_full(self):
        a = self
        addrs = [a]
        while a.parent_id:
            a = a.parent
            addrs.append(a)
        addrs.reverse()
        return addrs
    
    @classmethod
    def refresh_allsubids(clz):
        '''刷新全部字符类ID'''
        from third.funcs import list2trees, treechildren
        allcat = clz.objects.all().values_list('id', 'parent_id')
        trs = list2trees(allcat)
        d = {}
        for tr in trs:
            treechildren(tr, d)
        for k, v in d.items():
            clz.objects.filter(id=k).update(subids=v)
        return len(d)
    
    def refresh_subids(self):
        '''刷新自身以及父节点subid'''
        clz = self.__class__
        subids = []
        for c in clz.objects.filter(parent=self):
            subids += c.get_subidarray()
            subids.append(c.id)
        self.subids = subids
        self.save()
        ids = [i for i in subids]
        ids.append(self.id)
        
        p = self.parent
        while p:
            p.subids = list(set(p.get_subidarray() + ids))
            p.save()
            p = p.parent
    
    def before_delete(self):
        '''节点删除前调用'''
        ids = [i for i in self.get_subidarray()]
        ids.append(self.id)
        
        p = self.parent
        ids = set(ids)
        while p:
            p.subids = list(set(p.get_subidarray()) - ids)
            p.save()
            p = p.parent
        
    def __unicode__(self):
        return '%s%s%s' % ('|' if self.level else '', '-' * self.level, self.name)

    @classmethod
    def get_allids(cls, ids):
        rids = []
        for o in cls.objects.filter(id__in=ids):
            if o.id not in rids:
                rids += o.get_subidarray()
        return list(set(rids))

class KeyValue(BaseModel):
    key = models.CharField(_('健'), max_length=255, db_index=True, unique=True)
    type = models.CharField(_('类型'), max_length=255, null=True, blank=True, default="text")
    name = models.CharField(_('名称'), max_length=255, null=True, blank=True)
    value = models.TextField(_('值'), max_length=65535, null=True, blank=True)
    other = models.CharField(_('附加'), max_length=255, null=True, blank=True)
    
    @property
    def depends(self):
        return self.other.split(';')[0] if self.other else None

    @property
    def attachs(self):
        rs = self.other.split(';') if self.other else []
        return rs[1] if len(rs) > 1 else None

    @property
    def attachssetting(self):
        attachs = self.attachs
        if attachs:
            import re
            return dict(re.findall('([^=^\s]+)\s*=\s*([^=^\s]*)', attachs))
        else:
            return {}

    @classmethod
    def listjson(cls, v):
        if type(v) != list:
            try:
                v = json.loads(v)
            except:
                v = []
        return v
    
    @classmethod
    def trystr(cls, v):
        try:
            return str(v)
        except:
            pass
        return unicode(v)
    
    @classmethod
    def safefloat(cls, v):
        try:
            return float(v)
        except:
            pass
        return 0
    
    @classmethod
    def safejson(cls, v):
        if isinstance(v, basestring):
            try:
                v = json.loads(v)
            except:
                v = {}
        return v
    
    @classmethod
    def trydatetime(cls, v):
        from base.utils import parse_datetime
        return parse_datetime(v)
            
    
    TYPE_MAP = {
                'text':lambda s: KeyValue.trystr(s) if s else "",
                'largetext':lambda s: KeyValue.trystr(s) if s else "",
                'int':lambda s: int(s) if s else 0,
                'float':lambda s: float(s) if s else 0.0,
                'bool':lambda s: s and s.upper() == "TRUE",
                'imagelinks':lambda s:KeyValue.listjson(s),
                'texts':lambda s:[v.strip() for v in s.split(';') if v.strip()],
                'ints':lambda s:[int(v.strip()) for v in s.split(';') if v.strip().isdigit()],
                'floats':lambda s:[KeyValue.safefloat(v) for v in s.split(';') if v.strip()],
                'fixfloats':lambda s:[KeyValue.safefloat(v) for v in s.split(';')],
                'keyvals':lambda s:KeyValue.listjson(s),
                'timesegs':lambda s:KeyValue.listjson(s),
                'time':lambda s:KeyValue.trystr(s),
                'json':lambda s:KeyValue.safejson(s),
                'datetime':lambda s:KeyValue.trydatetime(s),
                'date':lambda s:KeyValue.trystr(s),
                }
    
    def __unicode__(self):
        return u'%s(%s)' % (self.name, self.key)
    class Meta:
        verbose_name = _('设置')
        verbose_name_plural = _('设置')
        ordering = ['ordering']
        app_label = 'base'
    
    @property
    def pyvalue(self):
        return KeyValue.TYPE_MAP[self.type](self.value) if self.type in KeyValue.TYPE_MAP else None
    
    @classmethod
    def gen_setting(cls, dft=None, ckord=False, autodel=False):
        '''def=[(key,type,name,value,other)]'''
        kvs = dict((v[0], v) for v in dft) if dft else None
        ks = [v[0] for v in dft] if dft else None
        if autodel:
            KeyValue.objects.filter().exclude(key__in=ks).delete()
        query = KeyValue.objects
        if ks:
            query = query.filter(key__in=ks)
        res = {}
        items = [i for i in query]
        for i in items:
            if ks and i.key in ks:
                ks.remove(i.key)
            res[i.key] = i.pyvalue
        
        if ks:
            arr = []
            for k in ks:
                v = kvs[k]
                kv = KeyValue(key=k, type=v[1], name=v[2], value=v[3], other=v[4])
                arr.append(kv)
                res[k] = kv.pyvalue
            KeyValue.objects.bulk_create(arr)
        if ckord and dft:
            ks = [v[0] for v in dft]
            idic = dict([(i.key, i) for i in KeyValue.objects.filter(key__in=ks)])
            for ordering, di in enumerate(dft):
                key = di[0]
                if key in idic:
                    item = idic[key]
                    other = di[4]
                    name = di[2]
                    stype = di[1]
                    nordering = ordering + 1
                    if item.ordering != nordering or item.other != other or item.name != name or item.type != stype:
                        item.ordering = nordering
                        item.other = other
                        item.name = name
                        item.type = stype
                        item.save()
        return res


class DataDic(BaseModel):
    objects = StatusManager()
    raw_objects = models.Manager()
    status = models.IntegerField(_('状态'), default=StatusManager.STATUS_NORMAL, choices=StatusManager.STATUS_CHOICES, editable=False)
    
    type = bfield.NameField(_('类型'))
    value = bfield.NameField(_('数据'))
    json = bfield.JsonField(_('附加'), default={})
    
    def __unicode__(self):
        return u'%s: %s' % (self.type, self.value)
    
    def to_json(self):
        return {
                'id':self.id,
                'value':self.value
                }
    
    class Meta:
        verbose_name = _('数据字典')
        verbose_name_plural = _('数据字典')
        ordering = ['ordering']
        app_label = 'base'

class XAreaMixin(object):
    @classmethod
    def wrap_xarea_query(cls, query, xme):
        return query.filter(area_id__in = xme.xarea_ids)










