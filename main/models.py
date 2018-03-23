# -*- coding: UTF-8 -*
'''
@author: Robin
'''

from django.db import models
from base.models import BaseModel
import datetime

def _(s):
    return s

class Note(BaseModel):
    date = models.DateField(_('日期'), default=datetime.date.today, db_index=True)
    type = models.CharField(_('类型'), max_length=255, blank=True, null=True)
    title = models.CharField(_('标题'), max_length=255, blank=True, null=True)
    content = models.TextField(_('正文'), max_length=65535, blank=True, null=True)
    icon = models.CharField(_('图标'), max_length=255, blank=True, null=True)
    image = models.CharField(_('图片'), max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _('记录')
        verbose_name_plural = _('记录')
        app_label = 'main'
        ordering = ['date', 'ordering', 'id']

    def to_json(self):
        from base.utils import obj2dic
        return obj2dic(self, ['id', 'date', 'type', 'title', 'content', 'icon', 'image'])