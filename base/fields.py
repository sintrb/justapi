# -*- coding: UTF-8 -*
'''
Copyright 2016 INRUAN Technology Co., Ltd. All rights reserved.

Created on 2016-10-22

@author: Robin
'''

from django.db import models
from django.db.models.fields import related
import json

def _(v):
    return v

def get_kwargs(**kwargs):
    return kwargs

def NameField(fieldname, **kwargs):
    for k, v in get_kwargs(db_index=True, null=False, blank=False, max_length=255).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.CharField(fieldname, **kwargs)

def IndexNameField(fieldname, **kwargs):
    for k, v in get_kwargs(db_index=True, null=False, blank=False, max_length=255).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.CharField(fieldname, **kwargs)

def SmallNameField(fieldname, **kwargs):
    for k, v in get_kwargs(db_index=True, null=False, blank=False, max_length=64).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.CharField(fieldname, **kwargs)

def SmallTextField(fieldname, **kwargs):
    for k, v in get_kwargs(null=True, blank=True, max_length=64).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.CharField(fieldname, **kwargs)

def NormalTextField(fieldname, **kwargs):
    for k, v in get_kwargs(null=True, blank=True, max_length=255).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.CharField(fieldname, **kwargs)

def DecimalField(fieldname, **kwargs):
    for k, v in get_kwargs(default=0, max_digits=20, decimal_places=2).items():
        if k not in kwargs:
            kwargs[k] = v
    return models.DecimalField(fieldname, **kwargs)

class BField(models.TextField):
    '''自定义基类'''
    __metaclass__ = models.SubfieldBase
    def __init__(self, verbose_name=None, name=None, primary_key=False,
        max_length=65535, unique=False, blank=True, null=True,
        db_index=False, rel=None, default=models.NOT_PROVIDED, editable=True,
        serialize=True, unique_for_date=None, unique_for_month=None,
        unique_for_year=None, choices=None, help_text='', db_column=None,
        db_tablespace=None, auto_created=False, validators=[],
        error_messages=None):
        models.TextField.__init__(self, verbose_name=verbose_name, name=name, primary_key=primary_key, max_length=max_length, unique=unique, blank=blank, null=null, db_index=db_index, rel=rel, default=default, editable=editable, serialize=serialize, unique_for_date=unique_for_date, unique_for_month=unique_for_month, unique_for_year=unique_for_year, choices=choices, help_text=help_text, db_column=db_column, db_tablespace=db_tablespace, auto_created=auto_created, validators=validators, error_messages=error_messages)
    description = "BField"
    def value_to_string(self, obj):
        return self.get_prep_value(self._get_val_from_obj(obj))

class LargeTextField(BField):
    '''长文本'''
    __metaclass__ = models.SubfieldBase
    description = "BLargeTextField"

class FullTextField(BField):
    '''富文本'''
    __metaclass__ = models.SubfieldBase
    description = "BFullTextField"

class ImageField(BField):
    '''图片字段'''
    __metaclass__ = models.SubfieldBase
    description = "BImage"
    def __init__(self, verbose_name=None, **kwargs):
        if 'aspectRatio' in kwargs:
            self.aspectRatio = kwargs.pop('aspectRatio')
        BField.__init__(self, verbose_name=verbose_name, **kwargs)

class LogoField(BField):
    '''图片字段'''
    __metaclass__ = models.SubfieldBase
    description = "BLogo"
    def __init__(self, verbose_name=None, **kwargs):
        if 'aspectRatio' in kwargs:
            self.aspectRatio = kwargs.pop('aspectRatio')
        BField.__init__(self, verbose_name=verbose_name, **kwargs)

class FileField(BField):
    '''文件上传字段'''
    __metaclass__ = models.SubfieldBase
    description = "BUploadFile"

class JsonField(BField):
    '''JSON字段'''
    __metaclass__ = models.SubfieldBase
    description = "BJsonField"
    def __init__(self, verbose_name=None, **kwargs):
        if 'editable' not in kwargs:
            kwargs['editable'] = False
        BField.__init__(self, verbose_name=verbose_name, **kwargs)
    def to_python(self, value):
#         print 'to_python1', value, type(value)
        v = models.TextField.to_python(self, value)
        if isinstance(v, basestring):
            try:
                v = json.loads(v.strip('"\'\\'))
            except Exception, e:
#                 print e
                pass
#         print 'to_python2', v, type(v)
        return v
    def get_prep_value(self, value):
#         print 'get_prep_value1', value, type(value)
        value = self.to_python(value)
        from utils import json_filed_default
        v = json.dumps(value, default=json_filed_default)
#         print 'get_prep_value2', v, type(v)
        return v
    def value_to_string(self, obj):
#         print 'value_to_string1', obj, type(obj)
        v = self.get_prep_value(self._get_val_from_obj(obj))
#         print 'value_to_string2', type(v)
        return v

class FilesField(JsonField):
    '''多个文件上传'''
    __metaclass__ = models.SubfieldBase
    description = "BUploadFiles"
    def __init__(self, verbose_name=None, **kwargs):
        if 'editable' not in kwargs:
            kwargs['editable'] = True
        JsonField.__init__(self, verbose_name=verbose_name, **kwargs)
#     {
#      'name':'file name',
#      'url':'file url'
#      ...
#      }

class LinksField(JsonField):
    '''链接集合'''
    __metaclass__ = models.SubfieldBase
    description = "BLinksField"
    def __init__(self, verbose_name=None, **kwargs):
        if 'editable' not in kwargs:
            kwargs['editable'] = True
        JsonField.__init__(self, verbose_name=verbose_name, **kwargs)
#     {
#      'name':'link name',
#      'url':'link url'
#      ...
#      }

class ImagesField(LargeTextField):
    '''多图片字段'''
    __metaclass__ = models.SubfieldBase
    description = "BImages"
    def __init__(self, verbose_name=None, **kwargs):
        if 'editable' not in kwargs:
            kwargs['editable'] = True
        if 'aspectRatio' in kwargs:
            self.aspectRatio = kwargs.pop('aspectRatio')
        LargeTextField.__init__(self, verbose_name=verbose_name, **kwargs)


class ForeignKeys(LargeTextField):
    '''多外键字段'''
    __metaclass__ = models.SubfieldBase
    description = "ForeignKeys"
    def __init__(self, verbose_name=None, **kwargs):
#         if 'to' in kwargs:
        self.tomodel = kwargs.pop('to', None)
        self.tomodelname = self.tomodel and self.tomodel.__name__
        self.toname = kwargs.pop('attr', 'name')
        self.showfields = kwargs.pop('showfields', 'id,name')
        LargeTextField.__init__(self, verbose_name=verbose_name, **kwargs)

from django.db.models import Lookup
from django.db.models.fields import Field

@Field.register_lookup
class BetweenLookup(Lookup):
    lookup_name = 'between'
    def get_prep_lookup(self):
        if isinstance(self.rhs, basestring):
            import re
            vs = re.findall(r'([\d\.]+)', self.rhs)
        else:
            vs = self.rhs
        return [r for r in vs]
    def get_db_prep_lookup(self, value, connection):
        return ['%s', value]
    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        _, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        if len(rhs_params) >= 2:
            res = '%s >= %%s and %s <= %%s' % (lhs, lhs), params[0:2]
        elif len(rhs_params) == 1:
            res = '%s = %%s' % (lhs), params[0:1]
        else:
            raise Exception(u'value error %s' % rhs_params)
        return res

class CachedReverseSingleRelatedObjectDescriptor(related.ReverseSingleRelatedObjectDescriptor):
    def __init__(self, field, timeout=60 * 10):
        self.timeout = timeout
        super(CachedReverseSingleRelatedObjectDescriptor, self).__init__(field)
    def __get__(self, instance, instance_type=None):
        if instance is None:
            return self
        if not self.field.related_fields:
            return None
        from base.utils import get_cached_obj
        lh_field, _ = self.field.related_fields[0]
        objid = getattr(instance, lh_field.attname)
        return get_cached_obj(self.field.rel.to, objid=objid, timeout=self.timeout)

class ForeignKey(models.ForeignKey):
    pass

class CachedForeignKey(ForeignKey):
    def __init__(self, to, to_field=None, rel_class=related.ManyToOneRel, db_constraint=True, **kwargs):
        self.timeout = kwargs.pop('timeout', 60 * 10)
        super(CachedForeignKey, self).__init__(to, to_field, rel_class, db_constraint, **kwargs)
        
    def contribute_to_class(self, cls, name, virtual_only=False):
        super(CachedForeignKey, self).contribute_to_class(cls, name, virtual_only=virtual_only)
        setattr(cls, self.name, CachedReverseSingleRelatedObjectDescriptor(self, self.timeout))


class SField(models.CharField):
    '''自定义基类'''
    __metaclass__ = models.SubfieldBase
    def __init__(self, verbose_name=None, name=None, primary_key=False,
        max_length=255, unique=False, blank=True, null=True):
        models.CharField.__init__(self, verbose_name=verbose_name, name=name, primary_key=primary_key, max_length=max_length, unique=unique, blank=blank, null=null)

class MultiSelectField(SField):
    '''多字段选择'''
    __metaclass__ = models.SubfieldBase
    description = "MultiSelectField"

    @property
    def selections(self):
        selections = self._selections() if callable(self._selections) else self._selections
        return [(u'[%s]' % v, n) for v,n in selections]

    def __init__(self, verbose_name=None, **kwargs):
        self._selections = kwargs.pop('selections', [])
        SField.__init__(self, verbose_name=verbose_name, **kwargs)
    def get_prep_value(self, value):
        value = self.to_python(value)
        return value or None
    def value_to_string(self, obj):
        v = self.get_prep_value(self._get_val_from_obj(obj))
        return v