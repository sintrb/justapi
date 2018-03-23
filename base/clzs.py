# -*- coding: UTF-8 -*
'''
Created on 2016年06月25日

@author: Robin
'''
import logging
from django.utils.encoding import force_text
from django.contrib.sessions import middleware
from django.core.exceptions import SuspiciousOperation
from django.contrib.sessions.backends.db import SessionStore,Session
from django.conf import settings
from django.utils import timezone

class ApiSessionStore(SessionStore):
    def load(self):
        try:
            s = Session.objects.get(
                session_key=self.session_key,
                expire_date__gt=timezone.now()
            )
            return self.decode(s.session_data)
        except (Session.DoesNotExist, SuspiciousOperation) as e:
            if isinstance(e, SuspiciousOperation):
                logger = logging.getLogger('django.security.%s' % 
                        e.__class__.__name__)
                logger.warning(force_text(e))
            return {}

class ApiSessionMiddleware(middleware.SessionMiddleware):
    def process_request(self, request):
        session_key = request.POST.get('_token') or request.GET.get('_token') or request.COOKIES.get(settings.SESSION_COOKIE_NAME, None) or request.COOKIES.get('_token')
        request.session = ApiSessionStore(session_key)

