#!/usr/bin/env python
import os
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

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "justapi.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
