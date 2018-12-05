# -*- coding: UTF-8 -*
'''
@author: Robin
'''
from base.views import ApiView, asapi

unlogin = asapi(logined=False)


class ApiView(ApiView):
    def get_meid(self):
        return 0

    @unlogin
    def getQiniuToken(self):
        '''获取七牛上传凭证'''
        return {
            'token': self.site.qiniuuploadtoken
        }

    @unlogin
    def getUploadToken(self):
        '''获取上传凭证'''
        return {
            'token': self.site.qiniuuploadtoken if self.site.setting.get('qiniu_enable') else 'inner',
            'action': self.site.setting.get('irfile_upload_path') or (self.site.setting.get('qiniu_enable') and 'http://upload.qiniu.com/') or '/utils/upload.html'
        }

    @unlogin
    def getnote(self, _param):
        '''获取记录'''
        return self.getNote(_param)

    @unlogin
    def getNote(self, _param):
        '''获取记录'''
        from base.utils import warp_query
        from main.models import Note
        query = Note.objects.filter()
        return warp_query(query, param=_param).last()

    @unlogin
    def saveNote(self, _param):
        '''保存记录'''
        from base.utils import dic2obj
        from main.models import Note
        note = _param.get('id') and Note.objects.filter(id=_param['id']).first() or Note()
        dic2obj(note, ['date', 'title', 'content', 'type', 'icon', 'image'], _param)
        note.save()
        return note
