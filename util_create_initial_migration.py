import os
import re
import settings

for app_name in settings.INSTALLED_APPS:
    if app_name not in ['noomake', 'ieeetags.site_admin']:
        # Get the last part after the last period (ie. django.contrib.admin -> admin)
        name = re.search('([^.]+)$', app_name).group(1)
        cmd = 'manage.py dmigration app %s' % name
        print 'cmd:', cmd
        os.system(cmd)
