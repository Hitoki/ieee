from datetime import datetime
import time
from django.db import models
from django.db.models import Q


class FailedLoginLogManager(models.Manager):

    def check_if_disabled(self, username, ip):
        "Return True if a given username or ip has been disabled."
        #log('check_if_disabled()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)
        ## log('  FailedLoginLog.DISABLE_ACCOUNT_TIME: %s' %
        ##     FailedLoginLog.DISABLE_ACCOUNT_TIME)
        before = datetime.fromtimestamp(time.time() -
                                        FailedLoginLog.DISABLE_ACCOUNT_TIME)
        #log('  before: %s' % before)
        ##log('  datetime.now(): %s' % datetime.now())
        if username is not None:
            num = self.filter(
                Q(username=username) | Q(ip=ip),
                disabled=True,
                date_created__gt=before,
            ).count()
            #log('  num: %s' % num)
            return num > 0
        else:
            num = self.filter(
                ip=ip,
                disabled=True,
                date_created__gt=before,
            ).count()
            #log('  num: %s' % num)
            return num > 0

    def add_and_check_if_disabled(self, username, ip):
        """Records a bad login and checks if the max has been reached.
        Returns True if user is under the limit, and False if user is over
        the limit."""
        self._add_failed_login(username, ip)
        return self.check_if_disabled(username, ip)

    def _add_failed_login(self, username, ip):
        "Adds a bad login entry and disables an account if necessary."

        #log('_add_failed_login()')
        #log('  username: %s' % username)
        #log('  ip: %s' % ip)

        # Check if there have been too many bad logins (including this one)
        before = datetime.fromtimestamp(time.time() -
                                        FailedLoginLog.FAILED_LOGINS_TIME)
        num_failed_logins = self.filter(
            Q(username=username) | Q(ip=ip),
            date_created__gt = before,
        ).count()
        #log('  num_failed_logins: %s' % num_failed_logins)

        if num_failed_logins >= FailedLoginLog.FAILED_LOGINS_MAX - 1:
            disabled = True
        else:
            disabled = False

        #log('  disabled: %s' % disabled)

        # Add a log entry for this failed entry
        log = self.create(
            username = username,
            ip = ip,
            disabled = disabled,
        )
        log.save()

        return disabled


class FailedLoginLog(models.Model):
    '''Keeps track of past failed logins.
    Suspends future logins for a certain time if there are too many
    failed logins.'''

    # This is the number of seconds in the past to check for bad logins
    FAILED_LOGINS_TIME = 10 * 60
    # The number of minutes to disable an account for
    DISABLE_ACCOUNT_TIME = 10 * 60
    # Max number of bad logins within the FAILED_LOGIN_TIME above
    FAILED_LOGINS_MAX = 10

    username = models.CharField(max_length=30)
    ip = models.CharField(max_length=16)
    disabled = models.BooleanField()
    date_created = models.DateTimeField(auto_now_add=True)

    objects = FailedLoginLogManager()


class UrlCheckerLog(models.Model):
    'Keeps track of the current URL-checking thread\'s status.'
    date_started = models.DateTimeField(auto_now_add=True)
    date_ended = models.DateTimeField(blank=True, null=True)
    date_updated = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=1000)


class ProfileLog(models.Model):
    'Debugging class, used to keep track of profiling pages.'
    url = models.CharField(max_length=1000)
    elapsed_time = models.FloatField()
    user_agent = models.CharField(max_length=1000)
    category = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def short_user_agent(self):
        short_user_agent1 = self.user_agent
        import re
        match = re.search(r'Chrome/([\d.]+)', self.user_agent)
        if match:
            short_user_agent1 = 'Chrome %s' % (match.group(1))
        else:
            match = re.search(r'Safari/([\d.]+)', self.user_agent)
            if match:
                short_user_agent1 = 'Safari %s' % (match.group(1))
            else:
                match = re.search(r'Firefox/([\d.]+)', self.user_agent)
                if match:
                    short_user_agent1 = 'Firefox %s' % (match.group(1))
                else:
                    match = re.search(r'MSIE ([\d.]+)', self.user_agent)
                    if match:
                        short_user_agent1 = 'MSIE %s' % (match.group(1))
        return short_user_agent1

    def __str__(self):
        return '<%s: %s, %s, %s>' % (self.__class__.__name__, self.url,
                                     self.elapsed_time,
                                     self.short_user_agent())
