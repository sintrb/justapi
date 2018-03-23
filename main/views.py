# -*- coding: UTF-8 -*
'''
@author: Robin
'''
from base.views import ApiView, asapi
class ApiView(ApiView):
    def get_meid(self):
        return 0

    @asapi(logined=False)
    def getnote(self):
        from main.models import Note
        return Note.objects.filter().last()
