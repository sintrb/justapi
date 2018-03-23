"""justapi URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
import sys
reload(sys)
class Sys:
    def setdefaultencoding(self):
        pass
sysx = sys
try:
    sysx.setdefaultencoding('utf8')
except:
    pass
from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from main.views import ApiView as MainApiView
urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^(?P<apiname>\S*)', csrf_exempt(MainApiView.as_view())),
]
