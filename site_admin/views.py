from datetime import datetime
import codecs
import csv
import hashlib
import logging
import math
import random
import re
import smtplib
import string
import StringIO
import threading
import time
import urllib
from urllib import quote, urlencode
import warnings
from Queue import Empty, Queue

from django.db import IntegrityError
from django.db import transaction
from django.core.mail import EmailMessage
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.utils import simplejson as json

from ieeetags import settings
from ieeetags import permissions
from ieeetags import url_checker
from ieeetags.util import *
from ieeetags.models import Node, NodeType, Permission, Resource, ResourceType, Society, Filter, Profile, get_user_from_username, get_user_from_email, UserManager, FailedLoginLog, UrlCheckerLog
#from ieeetags.logger import log
from ieeetags.views import render
from ieeetags.widgets import DisplayOnlyWidget
from forms import *
from widgets import make_display_only

_IMPORT_SOURCES = [
    'comsoc',
    'v.7',
]

def _get_version():
    #logging.debug('_get_version()')
    path = relpath(__file__, '..')
    version_path = relpath(__file__, '../version.txt')
    #logging.debug('  path: %s' % path)
    #logging.debug('  version_path: %s' % version_path)
    
    
    file = open(version_path, 'r')
    version = file.readline().strip()
    revision = file.readline().strip()
    date = file.readline().strip()
    file.close()
    #logging.debug('  revision: %s' % revision)
    if revision == '$WCREV$':
        revision = 'SVN'
        #logging.debug('  looking for svn revision')
        
        from subprocess import Popen, PIPE
        try:
            #logging.debug('  running:')
            #logging.debug('svn info "%s"' % path)
            proc = Popen('svn info "%s"' % path, shell=True, stdout=PIPE)
            #logging.debug('  wait')
            proc.wait()
            #logging.debug('  done wait')
            for line in proc.stdout:
                #logging.debug('  line: %s' % line)
                matches = re.match(r'Revision: (\d+)', line)
                if matches:
                    revision = matches.group(1) + '-svn'
                matches = re.match(r'Last Changed Date: (\S+ \S+)', line)
                if matches:
                    date = matches.group(1)
                    # NOTE: This is only supported in Python v2.5
                    #date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
                    date = datetime(*(time.strptime(date, '%Y-%m-%d %H:%M:%S')[0:6]))
        except Exception, e:
            #logging.debug('  got exception: %s' % e)
            revision = 'UNKNOWN'
            date = ''
        #logging.debug('  revision: %s' % revision)
        #logging.debug('  date: %s' % date)
            
    return version, revision, date

def _update_node_totals(nodes):
    for node in nodes:
        node.save()
    
def _unicode_csv_reader(unicode_csv_data, dialect=csv.excel, **kwargs):
    # csv.py doesn't do Unicode; encode temporarily as UTF-8:
    csv_reader = csv.reader(_utf_8_encoder(unicode_csv_data), dialect=dialect, **kwargs)
    for row in csv_reader:
        # decode UTF-8 back to Unicode, cell by cell:
        yield [unicode(cell, 'utf-8') for cell in row]

def _utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')

# Return a random selection from the given list
def _random_slice_list(list, min, max):
    list1 = list[:]
    count = random.randrange(min, max+1)
    random.shuffle(list1)
    return list1[:count]

def _split_no_empty(string, char):
    "Just like string.split(), except that an empty string results in an empty list []."
    if string.strip() == '':
        return []
    else:
        return string.split(char)

def _open_unicode_csv_reader(filename):
    "Opens a file as a unicode CSV.  Returns a (file, reader) tuple."
    file = codecs.open(filename, 'r', 'utf8')
    # Skip the UTF-8 BOM
    strip_bom(file)
    # Use a unicode csv reader:
    reader = _unicode_csv_reader(file)
    reader.next()
    return (file, reader)

def _open_unicode_csv_reader_for_file(file):
    "Opens a unicode CSV reader for the given file."
    #file = codecs.open(filename, 'r', 'utf8')
    # Skip the UTF-8 BOM
    strip_bom(file)
    # Use a unicode csv reader:
    reader = _unicode_csv_reader(file)
    reader.next()
    return reader

def _open_unicode_csv_writer(filename):
    "Opens a file as a unicode CSV.  Returns a (file, writer) tuple."
    file = codecs.open(filename, 'w', 'utf8')
    
    # Use a unicode csv writer:
    writer = csv.writer(file)
    return (file, writer)

def _check_tags_in_same_sector(tag1, tag2):
    for sector in tag1.parents.all():
        if sector in tag2.parents.all():
            return True
    return False

def _send_password_reset_email(request, user):
    if user.get_profile().reset_key is None:
        profile = user.get_profile()
        
        hash = hashlib.md5()
        hash.update(str(random.random()))
        hash = hash.hexdigest()
        
        profile.reset_key = hash
        profile.save()
    
    abs_reset_url = request.build_absolute_uri(reverse('password_reset', args=[user.id, user.get_profile().reset_key]))
    
    subject = 'Password reset confirmation'
    message = """You have requested to reset your password for the IEEE Technology Navigator.
    
To complete this request and reset your password, please click on the link below:
%s

If you did not request this password reset, simple ignore this email.

Username: %s
Email: %s
""" % (abs_reset_url, user.username, user.email)
    
    logging.debug('settings.DEFAULT_FROM_EMAIL: %s' % settings.DEFAULT_FROM_EMAIL)
    logging.debug('user.email: %s' % user.email)
    logging.debug('subject: %s' % subject)
    logging.debug('message: %s' % message)
    logging.debug('Sending email...')
    
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def _send_password_change_notification(user):
    subject = 'Your password has been changed'
    message = """The password on your account has been changed.  Please use the new password to login to your account.
"""
    
    logging.debug('settings.DEFAULT_FROM_EMAIL: %s' % settings.DEFAULT_FROM_EMAIL)
    logging.debug('user.email: %s' % user.email)
    logging.debug('subject: %s' % subject)
    logging.debug('message: %s' % message)
    logging.debug('Sending email...')

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def _escape_csv_field(value, add_quotes=True):
    if value is None:
        value = ''
    elif type(value) is bool:
        if value == True:
            value = 'yes'
        elif value == False:
            value = 'no'
        else:
            raise Exception('Unknown boolean value "%s"' % value)
    value = unicode(value).replace(u'"', u'""')
    if add_quotes:
        return '"%s"' % value
    else:
        return '%s' % value

def _escape_csv_list(list1, add_quotes=True):
    results = []
    for item in list1:
        if u',' in item:
            raise Exception('Found a comma in a CSV list value: %s' % item)
        results.append(_escape_csv_field(item, False))
    if add_quotes:
        return '"%s"' % ','.join(results)
    else:
        return '%s' % ','.join(results)

def list_to_html_list(list, className=''):
    "Convert a python list to an HTML UL list."
    list = ['<li>%s</li>' % item for item in list]
    if len(list) > 0:
        if className != '':
            className = ' class="%s"' % className
        list = '<ul%s>' % className + '\n'.join(list) + '</ul>'
    else:
        list = ''
    return list
    
def _failed_logins(request):
    """
    Shows the failed login page.
    NOTE: This page does not have its own URL.  Instead, it is rendered directly from a view like this:
        return _failed_logins(request)
    That way the browser's URL is preserved.  If a user reloads the page after the timeout, they reload the original URL and not the failed logins page.
    """
    next = request.GET.get('next', reverse('admin_home'))
    return render(request, 'site_admin/failed_logins.html', {
        'next': next,
        'FAILED_LOGINS_TIME_MINUTES': FailedLoginLog.FAILED_LOGINS_TIME / 60,
    })

def _parse_tristate_value(value):
    assert isinstance(value, basestring)
    if value == 'no change':
        return None
    elif value == 'yes':
        return True
    elif value == 'no':
        return False
    else:
        raise Exception('Unknown value "%r"' % value)

def society_manager_or_admin_required(fn):
    """
    This is used as a decorator.  The decorated view is restricted to users with the role of society manager, society admin, or admin.  Other roles are sent to the "permission denied" page.
    This should be used in conjunction with the @login_required decorator.
    """
    def _decorator_society_manager_or_admin_required(request, *args, **kwargs):
        if not request.user.is_anonymous() and (request.user.get_profile().role in [Profile.ROLE_ADMIN, Profile.ROLE_SOCIETY_ADMIN, Profile.ROLE_SOCIETY_MANAGER]):
            # User is an admin or society manager, allow
            return fn(request, *args, **kwargs)
        else:
            # Disallow
            return permission_denied(request)
    return _decorator_society_manager_or_admin_required

def society_admin_or_admin_required(fn):
    """
    This is used as a decorator.  The decorated view is restricted to users with the role of society admin or admin.  Other roles are sent to the "permission denied" page.
    This should be used in conjunction with the @login_required decorator.
    """
    def _decorator_society_admin_or_admin_required(request, *args, **kwargs):
        if not request.user.is_anonymous() and (request.user.get_profile().role in [Profile.ROLE_ADMIN, Profile.ROLE_SOCIETY_ADMIN]):
            # User is an admin or society manager, allow
            return fn(request, *args, **kwargs)
        else:
            # Disallow
            return permission_denied(request)
    return _decorator_society_admin_or_admin_required

def admin_required(fn):
    """
    This is used as a decorator.  The decorated view is restricted to users with the role of admin only.  Other roles are send to the "permission denied" page.
    This should be used in conjunction with the @login_required decorator.
    """
    def _decorator_admin_required(request, *args, **kwargs):
        if not request.user.is_anonymous() and (request.user.get_profile().role in [Profile.ROLE_ADMIN]):
            # User is an admin, allow
            return fn(request, *args, **kwargs)
        else:
            # Disallow
            return permission_denied(request)
    return _decorator_admin_required

# ------------------------------------------------------------------------------

def login(request):
    next = request.GET.get('next', '')
    remote_addr = request.META['REMOTE_ADDR']
    feedback = request.GET.get('feedback')
    
    # Check for too many bad logins from this IP
    if FailedLoginLog.objects.check_if_disabled(None, remote_addr):
        return _failed_logins(request)
    
    error = ''
    
    if request.method == 'GET':
        form = LoginForm()
    else:
        form = LoginForm(request.POST)
        
        # Grab the full "next" URL from the hidden form field, including the #hash part
        next = request.POST['next']
        
        # TODO: this hack is to account for the bug where the 'next' var has the hash instead of a real url
        if next.startswith('#'):
            next = ''
        
        if form.is_valid():
            user = auth.authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            
            username = form.cleaned_data['username']
            
            # If account is disabled, prevent from logging in
            if FailedLoginLog.objects.check_if_disabled(username, remote_addr):
                return _failed_logins(request)
            
            elif user is None:
                # Bad login
                
                # If too many bad logins, redirect to bad login page
                if FailedLoginLog.objects.add_and_check_if_disabled(username, remote_addr):
                    return _failed_logins(request)
                
                error = 'Invalid login, please try again.'
                
            elif user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER and user.societies.count() == 0:
                # Society Manage doesn't have an assigned society
                
                # If too many bad logins, redirect to bad login page
                if FailedLoginLog.objects.add_and_check_if_disabled(username, remote_addr):
                    return _failed_logins(request)
                
                error = 'Your account has not been assigned to a society yet.  Please contact the administrator to fix this.'
                
            else:
                # Successful login
                auth.login(request, user)
                
                profile = user.get_profile()
                profile.last_login_time = datetime.now()
                profile.save()
                
                if next != '':
                    return HttpResponseRedirect(next)
                elif user.get_profile().role == Profile.ROLE_ADMIN or user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
                    return HttpResponseRedirect(reverse('admin_home'))
                elif user.get_profile().role == Profile.ROLE_END_USER:
                    return HttpResponseRedirect(reverse('index'))
                else:
                    raise Exception('Unknown user role "%s"' % user.get_profile().role)
    
    return render(request, 'site_admin/login.html', {
        'error': error,
        'next': next,
        'show_society_login_banner': settings.SHOW_SOCIETY_LOGIN_BANNER,
        'form': form,
        'feedback': feedback,
    })

def logout(request):
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.last_logout_time = datetime.now()
        profile.save()
    auth.logout(request)
    return HttpResponseRedirect(reverse('admin_login') + '?feedback=1')

def forgot_password(request):
    cancel_page = request.GET.get('cancel_page', '')
    error = ''
    if request.method == 'GET':
        form = ForgotPasswordForm()
    else:
        form = ForgotPasswordForm(request.POST)
        
        if form.is_valid():
            
            if form.cleaned_data['username'].strip() != '':
                username = form.cleaned_data['username']
                user = get_user_from_username(username)
                if user is None:
                    error = '<ul class="error"><li>The username "%s" was not found.</li></ul>' % username
                elif user.email is None or user.email.strip() == '':
                    error = '<ul class="error"><li>The account with username "%s" does not have a valid email.</li></ul>' % username
                else:
                    try:
                        _send_password_reset_email(request, user)
                    except smtplib.SMTPRecipientsRefused, e:
                        error = 'Recipients refused'
                    except smtplib.SMTPException, e:
                        error = str(type(e))
                        #error = str(type(e)) + ': ' + str(e)
                    else:
                        error = None
                    url = reverse('forgot_password_confirmation')
                    if error is not None:
                        logging.error('Error sending reset email: %s: %s' % (type(e), e))
                        url += '?error=' + quote(error)
                    return HttpResponseRedirect(url)
                    
            elif form.cleaned_data['email'].strip() != '':
                email = form.cleaned_data['email']
                user = get_user_from_email(email)
                if user is None:
                    error = '<ul class="error"><li>The email "%s" was not found.</li></ul>' % email
                else:
                    _send_password_reset_email(request, user)
                    return HttpResponseRedirect(reverse('forgot_password_confirmation'))
                    
            else:
                error = '<ul class="error"><li>You must fill in one of the fields below.</li></ul>'
        
    return render(request, 'site_admin/forgot_password.html', {
        'error': error,
        'form': form,
        'cancel_page': cancel_page,
    })

def forgot_password_confirmation(request):
    error = request.GET.get('error', None)
    return render(request, 'site_admin/forgot_password_confirmation.html', {
        'error': error,
    })

def password_reset(request, user_id, reset_key):
    user = User.objects.get(id=user_id)
    profile = user.get_profile()
    
    if profile.reset_key is not None and reset_key == profile.reset_key:
        # Got the right reset key
        error = ''
        if request.method == 'GET':
            form = ChangePasswordForm()
        else:
            form = ChangePasswordForm(request.POST)
            if form.is_valid():
                if form.cleaned_data['password1'].strip() == '':
                    error = '<ul class="error"><li>The password cannot be blank.</li></ul>'
                elif form.cleaned_data['password1'] != form.cleaned_data['password2']:
                    error = '<ul class="error"><li>The passwords did not match.</li></ul>'
                else:
                    profile.reset_key = None
                    profile.save()
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    return HttpResponseRedirect(reverse('password_reset_success'))
                    
        return render(request, 'site_admin/password_reset.html', {
            'error': error,
            'user_id': user_id,
            'reset_key': reset_key,
            'form': form,
        })
    else:
        return render(request, 'site_admin/password_reset_failure.html')

def password_reset_success(request):
    return render(request, 'site_admin/password_reset_success.html')

@login_required
def change_password(request):
    return_url = request.GET.get('return_url')
    if return_url is None:
        return_url = reverse('admin_home')
    
    error = ''
    if request.method == 'GET':
        form = ChangePasswordForm()
    else:
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            if form.cleaned_data['password1'].strip() == '':
                error = '<ul class="error"><li>The password cannot be blank.</li></ul>'
            elif form.cleaned_data['password1'] != form.cleaned_data['password2']:
                error = '<ul class="error"><li>The passwords did not match.</li></ul>'
            else:
                # Successfully changed password
                request.user.set_password(form.cleaned_data['password1'])
                request.user.save()
                
                # Send the password change email
                _send_password_change_notification(request.user)
                
                return HttpResponseRedirect(reverse('change_password_success') + '?' + urlencode({'return_url': return_url}))
                
    return render(request, 'site_admin/change_password.html', {
        'error': error,
        'return_url': return_url,
        'form': form,
    })

@login_required
def change_password_success(request):
    return_url = request.GET.get('return_url')
    return render(request, 'site_admin/change_password_success.html', {
        'return_url': return_url,
    })

@login_required
@society_manager_or_admin_required
def home(request):
    role = request.user.get_profile().role
    
    if role == Profile.ROLE_ADMIN:
        # Show the admin home page
        version, revision, date = _get_version()
        
        num_societies = Society.objects.count()
        num_society_managers = UserManager.get_society_managers().count()
        num_sectors = Node.objects.getSectors().count()
        num_tags = Node.objects.getTags().count()
        num_resources = Resource.objects.count()
        
        return render(request, 'site_admin/admin_home.html', {
            'version': version,
            'revision': revision,
            'date': date,
            'num_societies': num_societies,
            'num_society_managers': num_society_managers,
            'num_sectors': num_sectors,
            'num_tags': num_tags,
            'num_resources': num_resources,
            'DEBUG_ENABLE_CLUSTERS': settings.DEBUG_ENABLE_CLUSTERS,
        })
        
    elif role == Profile.ROLE_SOCIETY_ADMIN:
        # Show list of societies
        return HttpResponseRedirect(reverse('admin_societies'))
        
    elif role == Profile.ROLE_SOCIETY_MANAGER:
        # Redirect to the society manager home page
        hash = request.GET.get('hash', '')
        
        # Only one society, just redirect to that view page
        if request.user.societies.count() == 1:
            return HttpResponseRedirect(reverse('admin_manage_society', args=[request.user.societies.all()[0].id]) + hash)
        
        # Has more than one society, show list of societies
        elif request.user.societies.count() > 1:
            return HttpResponseRedirect(reverse('admin_societies'))
        
        else:
            raise Exception('User is a society manager but is not assigned to any societies.')
    
    else:
        raise Exception('Unknown role %s' % role)

#@login_required
#def home_societies_list(request):
#    permissions.require_superuser(request)
#    
#    societies = Society.objects.getForUser(request.user)
#    return render(request, 'site_admin/home_societies_list.html', {
#        'societies': societies,
#    })

@login_required
@society_manager_or_admin_required
def missing_resource(request, society_id):
    if request.method == 'GET':
        form = MissingResourceForm(initial={
            'society': society_id,
            'name': request.user.username,
            'email': request.user.email,
        })
        
    else:
        form = MissingResourceForm(request.POST)
        if form.is_valid():
            society = Society.objects.get(id=society_id)
            
            # Make sure that user has permissions for the specified society
            assert(request.user.is_superuser or request.user.societies.filter(id=society.id).count() > 0)
            
            # Send email
            subject = 'Missing resource for "%s" society.' % request.user.username
            message = 'Sent on %s:\n' % time.strftime('%Y-%m-%d %H:%M:%S') \
                + 'From: %s (%s)\n' % (request.user.username, request.user.email) \
                + 'Type of resource: %s\n\n' % form.cleaned_data['resource_type'] \
                + 'Description:\n' \
                + '%s\n\n' % form.cleaned_data['description']
            send_from = settings.DEFAULT_FROM_EMAIL
            # Send this to the server admins and also Peter Wiesner (IEEE)
            send_to = settings.ADMIN_EMAILS + ['pwiesner@ieee.org']
            
            logging.debug('send_to: %s' % send_to)
            logging.debug('send_from: %s' % send_from)
            logging.debug('subject: %s' % subject)
            logging.debug('message: %s' % message)
            
            try:
                logging.debug('calling send_mail()')
                send_mail(subject, message, send_from, send_to)
            except Exception, e:
                logging.error('Error sending missing resource email: %s' % e)
                email_error = True
            else:
                email_error = False
            
            logging.debug('done sending email')
            
            return render(request, 'site_admin/missing_resource_confirmation.html', {
                'email_error': email_error,
            })
        
    return render(request, 'site_admin/missing_resource.html', {
        'form': form,
        'society_id': society_id,
    })

@login_required
def permission_denied(request):
    return render(request, 'site_admin/permission_denied.html')

@login_required
@society_manager_or_admin_required
@transaction.commit_on_success
def import_tags(request, source):
    logging.debug('import_tags()')
    start = time.time()
    
    if source == 'v.7':
        filename = relpath(__file__, '../data/v.7/2009-04-21 - tags.csv')
    elif source == 'comsoc':
        filename = relpath(__file__, '../data/comsoc/tags.csv')
    else:
        raise Exception('Unknown source "%s"' % source)
    
    logging.debug('  filename: %s' % filename)
    
    if source == 'comsoc':
        # DEBUG: For comsoc only:
        comsoc = Society.objects.all()[0]
    
    # DEBUG:
    DEBUG_MAX_ROWS = None
    #DEBUG_MAX_ROWS = 50
    
    row_count = 0
    tags_created = 0
    num_duplicate_tags = 0
    related_tags_assigned = 0
    duplicate_tags = ''
    
    # Import all tags
    if True:
        # Delete all existing tags
        Node.objects.getTags().delete()
    
        (file, reader) = _open_unicode_csv_reader(filename)
        for row in reader:
            # Tag,Sectors,Filters,Related Tags
            tag_name, sector_names, filter_names, related_tag_names = row
            tag_name = tag_name.strip()
            sector_names = [sector_name.strip() for sector_name in _split_no_empty(sector_names, ',')]
            filter_names = [filter_name.strip() for filter_name in _split_no_empty(filter_names, ',')]
            
            sectors = [Node.objects.get_sector_by_name(sector_name) for sector_name in sector_names]
            filters = [Filter.objects.getFromName(filter_name) for filter_name in filter_names]
            
            #logging.debug('    tag_name: %s' % tag_name)
            
            tag = Node.objects.get_tag_by_name(tag_name)
            
            if tag is not None:
                ## Found duplicate tag, don't insert
                #logging.error('    Duplicate tag "%s" found.' % tag_name)
                #duplicate_tags += '%s<br/>\n' % tag_name
                #num_duplicate_tags += 1
            
                # Tag already exists, add any sectors for the duplicate to the existing tag
                logging.debug('    Duplicate tag "%s" found.' % tag_name)
                duplicate_tags += '%s<br/>\n' % tag_name
                num_duplicate_tags += 1
                
                #logging.debug('      tag.parents.all(): %s' % tag.parents.all())
                #logging.debug('      sectors: %s' % sectors)
                
                for sector in sectors:
                    #if tag.parents.filter(id=sector.id).count() == 0:
                    #logging.debug('      adding sector: %s' % sector)
                    tag.parents.add(sector)
                
                #logging.debug('      tag.parents.all(): %s' % tag.parents.all())
                tag.save()
                
                #assert False
            
            else:
                # Tag is unique, insert it
            
                tag = Node.objects.create_tag(
                    name=tag_name,
                )
                #print '  sectors:', sectors
                tag.parents = sectors
                tag.filters = filters
                
                if settings.DEBUG_IMPORT_ASSIGN_ALL_TAGS_TO_COMSOC and source == 'comsoc':
                    # For the comsoc demo only, assign all tags to COMSOC society
                    tag.societies.add(comsoc)
                
                tag.save()
                tags_created += 1
                
            row_count += 1
            if not row_count % 50:
                logging.debug('    Parsing row %d, row/sec %f' % (row_count, row_count/(time.time()-start) ))
            
            if DEBUG_MAX_ROWS is not None and row_count > DEBUG_MAX_ROWS:
                logging.debug('  reached max row count of %d, breaking out of loop' % DEBUG_MAX_ROWS)
                break
            
        file.close()
        
    # Reparse the file to import related tags
    if True:
        logging.debug('  parsing related tags')
        
        # Now reopen the file to parse for related tags
        (file, reader) = _open_unicode_csv_reader(filename)
        
        row_count = 0
        related_tags_start = time.time()
        
        for row in reader:
            # Tag,Sectors,Filters,Related Tags
            tag_name, sector_names, filter_names, related_tag_names = row
            related_tag_names = [related_tag_name.strip() for related_tag_name in _split_no_empty(related_tag_names, ',')]
            
            # Continue if there are any related names to lookup
            if len(related_tag_names):
                tag_name = string.capwords(tag_name.strip())
                sector_names = [sector_name.strip() for sector_name in _split_no_empty(sector_names, ',')]
                
                tag = Node.objects.get_tag_by_name(tag_name)
                
                related_tags = []
                for related_tag_name in related_tag_names:
                    related_tag = Node.objects.get_tag_by_name(related_tag_name)
                    if related_tag is None:
                        raise Exception('Can\'t find matching related tag "%s"' % related_tag_name)
                    
                    if not _check_tags_in_same_sector(tag, related_tag):
                        raise Exception('Related tag "%s" is not in the same sector(s) as tag "%s".' % (related_tag, tag))
                    
                    related_tags.append(related_tag)
                
                tag.related_tags = related_tags
                related_tags_assigned += len(related_tags)
                tag.save()
                
            row_count += 1
            if not row_count % 50:
                try:
                    logging.debug('    Parsing row %d, row/sec %f' % (row_count, row_count/(time.time()-start) ))
                except:
                    pass
            
            if DEBUG_MAX_ROWS is not None and row_count > DEBUG_MAX_ROWS:
                logging.debug('  reached max row count of %d, breaking out of loop' % DEBUG_MAX_ROWS)
                break
                
        file.close()
    
    page_time = time.time()-start
    
    return render(request, 'site_admin/import_results.html', {
        'page_title': 'Import Tags',
        'results': {
            'page_time': page_time,
            'row_count': row_count,
            'tags_created': tags_created,
            'num_duplicate_tags': num_duplicate_tags,
            'related_tags_assigned': related_tags_assigned,
            'duplicate_tags': duplicate_tags,
        },
    })

@login_required
@admin_required
@transaction.commit_on_success
def unassigned_tags(request):
    logging.debug('unassigned_tags()')
    start = time.time()
    
    row_count = 0
    num_orphan_tags = 0
    orphan_tags = []
    
    tab_society = Society.objects.getFromAbbreviation('TAB')
    if tab_society is None:
        raise Exception('Can\'t find TAB society')
    
    tags = Node.objects.get_tags()
    for tag in tags:
        if tag.societies.count() == 0:
            # Found orphan tag, assign to TAB
            #print 'got emtpy one, %s' % tag.name
            orphan_tags.append(u'<li>%s</li>' % tag.name)
            tab_society.tags.add(tag)
            tab_society.save()
            num_orphan_tags += 1

    orphan_tags = u'<ul>\n' + u'\n'.join(orphan_tags) + u'</ul>\n'
    page_time = time.time()-start
    
    return render(request, 'site_admin/results.html', {
        'page_title': 'Unassigned Tags',
        'results': {
            'page_time': page_time,
            'orphan_tags': orphan_tags,
            'num_orphan_tags': num_orphan_tags,
        },
    })

def _remove_society_acronym(society_name):
    # Make sure the society name field does not contain a redundant acronym (there is already have an acronym field)
    matches = re.match(r'^(.+) \((.+)\)$', society_name)
    if matches is not None:
        society_name = matches.group(1)
    #logging.debug('society name: %s' % society_name)
    return society_name

def _import_societies(file1):
    # Get a unicode CSV reader
    reader = _open_unicode_csv_reader_for_file(file1)
    
    row_count = 0
    societies_created = 0
    societies_updated = 0
    errors = []
    
    for row in reader:
        # Name, Abbreviation, URL, Tags
        society_name, abbreviation, url = row
        society_name = society_name.strip()
        abbreviation = abbreviation.strip()
        url = url.strip()
        
        # Validation
        if url != '' and not url.startswith('http'):
            # URL doesn't start with "http", throw error
            errors.append('For "%s", url "%s" does not start with "http" or "https"' % (society_name, url))
        else:
            society = Society.objects.filter(name=society_name, abbreviation=abbreviation)
            assert society.count() >= 0 and society.count() <= 1
            if society.count() == 1:
                # Found matching society, update it
                #logging.debug('  updating society "%s" with url "%s"' % (society_name, url))
                society = society[0]
                
                society.url = url
                society.save()
                
                #logging.debug('    society.id: %s' % society.id)
                #logging.debug('    society.name: %s' % society.name)
                #logging.debug('    society.abbreviation: %s' % society.abbreviation)
                #logging.debug('    society.url: %s' % society.url)
                
                societies_updated += 1
            else:
                society_names = Society.objects.filter(name=society_name)
                society_abbreviations = Society.objects.filter(abbreviation=abbreviation)
                if society_names.count() > 0:
                    # Found a duplicate name
                    #logging.debug('Found a duplicate society name "%s", but the abbreviation "%s" did not match the file "%s"' % (society_name, society_names[0].abbreviation, abbreviation))
                    errors.append('Found a duplicate society name "%s", but the abbreviation "%s" did not match the file "%s"' % (society_name, society_names[0].abbreviation, abbreviation))
                elif society_abbreviations.count() > 0:
                    # Found a duplicate abbreviation
                    #logging.debug('Found a duplicate society abbreviation "%s", but the name "%s" did not match the file "%s"' % (abbreviation, society_abbreviations[0].name, society_name))
                    errors.append('Found a duplicate society abbreviation "%s", but the name "%s" did not match the file "%s"' % (abbreviation, society_abbreviations[0].name, society_name))
                else:
                    # No duplicates, so this is a new society
                    #logging.debug('Creating new society "%s", %s' % (society_name, abbreviation))
                    society = Society.objects.create(
                        name=society_name,
                        abbreviation=abbreviation,
                        url=url,
                    )
                    societies_created += 1
                
        #row_count += 1
        #if not row_count % 10:
        #    logging.debug('  Parsing row %d' % row_count)
    
    return {
        'row_count': row_count,
        'societies_created': societies_created,
        'societies_updated': societies_updated,
        'errors': errors,
    }
    
@login_required
@admin_required
@transaction.commit_manually
def import_societies(request):
    #logging.debug('import_societies()')
    if request.method == 'GET':
        # Display form
        form = ImportFileForm()
        return render(request, 'site_admin/import_file.html', {
            'page_title': 'Import Societies',
            'form': form,
            'submit_url': reverse('admin_import_societies'),
        })
        
    else:
        file1 = request.FILES['file']
        results = _import_societies(file1)
        
        if len(results['errors']) > 0:
            #logging.debug('Got errors, rolling back transaction')
            transaction.rollback()
        else:
            #logging.debug('Committing transaction')
            transaction.commit()
        
        errors = list_to_html_list(results['errors'], 'errors')
        del results['errors']
        
        return render(request, 'site_admin/import_file.html', {
            'page_title': 'Import Societies',
            'errors': errors,
            'results': results,
        })

@login_required
@admin_required
def fix_societies_import(request):
    start = time.time()
    
    in_filename = relpath(__file__, '../data/v.7/2009-04-20 - societies.csv')
    out_filename = relpath(__file__, '../data/v.7/2009-04-20 - societies - fixed.csv')
    
    # Get a unicode CSV reader
    (in_file, reader) = _open_unicode_csv_reader(in_filename)
    #(out_file, writer) = _open_unicode_csv_writer(out_filename)
    
    out_file = codecs.open(out_filename, 'w', encoding='utf-8')
    
    # Write the header row
    out_row = '"%s","%s","%s","%s"\r\n' % (
        'Name',
        'Abbreviation',
        'URL',
        'Tags',
    )
    out_file.write(out_row)
    
    row_count = 0
    
    for row in reader:
        
        
        society_name, abbreviation, url, tag_names1, tag_names2, tag_names3 = row
        tag_names1 = [tag.strip() for tag in _split_no_empty(tag_names1, ',')]
        tag_names2 = [tag.strip() for tag in _split_no_empty(tag_names2, ',')]
        tag_names3 = [tag.strip() for tag in _split_no_empty(tag_names3, ',')]
        
        tag_names = []
        tag_names.extend(tag_names1)
        tag_names.extend(tag_names2)
        tag_names.extend(tag_names3)
        
        # Filter out blank tag names
        tag_names = [tag_name for tag_name in tag_names if tag_name is not None and tag_name.strip() != '']
        
        tag_names = ', '.join(tag_names)
        
        # Manually output a CSV row (since the csv module doesn't support unicode)
        out_row = '"%s","%s","%s","%s"\r\n' % (
            society_name.replace('"', '""'),
            abbreviation.replace('"', '""'),
            url.replace('"', '""'),
            tag_names.replace('"', '""'),
        )
        out_file.write(out_row)
        
        row_count += 1
        #if not row_count % 10:
        #    print '  Parsing row %d' % row_count
        
    in_file.close()
    out_file.close()
    
    return render(request, 'site_admin/fix_societies_import.html', {
        'row_count': row_count,
        'page_time': time.time()-start,
    })
    
def _import_resources(file, batch_commits=False):
    #logging.debug('_import_resources()')
    
    start = time.time()
    
    row_count = 0
    duplicate_resources = 0
    resources_created = 0
    societies_assigned = 0
    num_invalid_societies = 0
    resources_skipped = 0
    
    #(file, reader) = _open_unicode_csv_reader(filename)
    reader = _open_unicode_csv_reader_for_file(file)
    
    valid_societies = {}
    invalid_societies = {}
    
    for row in reader:
        
        #Type, ID, Name, Description, URL, Tags, Society Abbreviations, Year, Standard Status, Technical Committees, Keywords, Priority, Completed, Project Code, Date
        type1, ieee_id, name, description, url, tag_names, society_abbreviations, year, standard_status, technical_committees, keywords, priority_to_tag, completed, project_code, date1 = row
        
        #logging.debug('    name: %s' % name)
        
        # Fix formatting
        if year == '':
            year = None
        else:
            year = int(year)
        name = name.strip()
        url = url.strip()
        society_abbreviations = [society_abbreviations.strip() for society_abbreviations in society_abbreviations.split(',')]
        standard_status = standard_status.strip()
        if date1.strip() == '':
            date1 = None
        else:
            date1 = datetime.strptime(date1, '%m/%d/%Y')
        
        resource_type = ResourceType.objects.getFromName(type1)
        
        if standard_status == '':
            standard_status = ''
        elif standard_status.lower() in Resource.STANDARD_STATUSES:
            standard_status = standard_status.lower()
        else:
            raise Exception('Unknown standard status "%s"' % standard_status)
        
        # Truncate keywords to 1000 chars
        keywords = keywords[:1000]
        
        if priority_to_tag.lower() == 'yes':
            priority_to_tag = True
        elif priority_to_tag.lower() == 'no':
            priority_to_tag = False
        else:
            raise Exception('Unknown priority "%s"' % priority_to_tag)
        
        if completed.lower() == 'yes':
            completed = True
        elif completed.lower() == 'no':
            completed = False
        else:
            raise Exception('Unknown priority "%s"' % completed)
        
        # Validate input
        if name.strip() == '':
            raise Exception('Resource name is blank for row: %s' % row)
        
        societies = []
        
        # Search by society abbreviation only
        for society_abbreviation in society_abbreviations:
            if society_abbreviation != '':
                society = Society.objects.getFromAbbreviation(society_abbreviation)
                if society is None:
                    if society_abbreviation not in invalid_societies:
                        invalid_societies[society_abbreviation] = 1
                    else:
                        invalid_societies[society_abbreviation] += 1
                    num_invalid_societies += 1
                    #logging.error('    Invalid society abbreviation "%s".' % society_abbreviation)
                else:
                    if society_abbreviation not in valid_societies:
                        valid_societies[society_abbreviation] = 1
                    else:
                        valid_societies[society_abbreviation] += 1
                    societies_assigned += 1
                    societies.append(society)
        
        # DEBUG: skip adding resource (for checking data)
        if True:
            
            if len(societies) == 0:
                # No valid societies, skip this resource
                resources_skipped += 1
                
            else:
                # Resource has valid societies, insert it
                
                if True:
                    num_existing = Resource.objects.filter(resource_type=resource_type, ieee_id=ieee_id).count()
                    if num_existing > 0:
                        #logging.debug('  DUPLICATE: resource "%s" already exists.' % name)
                        duplicate_resources += 1
                    
                    else:
                        #logging.debug('  Adding resource "%s"' % name)
                        #logging.debug('  project_code: %s' % project_code)
                        
                        resource = Resource.objects.create(
                            resource_type=resource_type,
                            ieee_id=ieee_id,
                            name=name,
                            description=description,
                            url=url,
                            year=year,
                            keywords=keywords,
                            priority_to_tag=priority_to_tag,
                            standard_status=standard_status,
                            completed=completed,
                            conference_series=project_code,
                            date=date1,
                        )
                        resource.societies = societies
                        resource.save()
                        resources_created += 1
                    
        if not row_count % 50:
            try:
                logging.debug('    Parsing row %d, row/sec %f' % (row_count, row_count/(time.time()-start) ))
            except Exception:
                pass
            
        row_count += 1
        
        if batch_commits and not row_count % 300:
            #logging.debug('    committing transaction.')
            transaction.commit()

    file.close()
    
    if batch_commits:
        logging.debug('    committing last transaction.')
        transaction.commit()
    
    results = '<table>\n'
    items = valid_societies.items()
    items.sort()
    for name,value in items:
        results += '<tr><td>%s</td><td>%s</td></tr>\n' % (name, value)
    results += '</table>\n'
    valid_societies = results
    
    results = '<table>\n'
    items = invalid_societies.items()
    items.sort()
    for name,value in items:
        results += '<tr><td>%s</td><td>%s</td></tr>\n' % (name, value)
    results += '</table>\n'
    invalid_societies = results
    
    #logging.debug('~_import_resources()')
    
    return {
        'row_count': row_count,
        'duplicate_resources': duplicate_resources,
        'resources_created': resources_created,
        'societies_assigned': societies_assigned,
        'num_invalid_societies': num_invalid_societies,
        'valid_societies': valid_societies,
        'invalid_societies': invalid_societies,
        'resources_skipped': resources_skipped,
    }

#@login_required
#@transaction.commit_manually
#def import_conferences(request, source):
#    permissions.require_superuser(request)
#    
#    start = time.time()
#    
#    if source not in _IMPORT_SOURCES:
#        raise Exception('Unknown import source "%s"' % source)
#    
#    if source == 'comsoc':
#        filename = relpath(__file__, '../data/comsoc/conferences.csv')
#    elif source == 'v.7':
#        filename = relpath(__file__, '../data/v.7/2009-04-21 - conferences.csv')
#
#    # Delete all conferences
#    Resource.objects.get_conferences().delete()
#    transaction.commit()
#    
#    # Import conferences
#    results = _import_resources(filename, batch_commits=True)
#    
#    results['page_time'] = time.time()-start
#    
#    return render(request, 'site_admin/import_results.html', {
#        'page_title': 'Import Conferences',
#        'results': results,
#    })

#@login_required
#@transaction.commit_on_success
#def import_periodicals(request, source):
#    permissions.require_superuser(request)
#    
#    start = time.time()
#    
#    if source not in _IMPORT_SOURCES:
#        raise Exception('Unknown import source "%s"' % source)
#    
#    if source == 'comsoc':
#        raise Exception('There is no periodicals file for COMSOC')
#    elif source == 'v.7':
#        filename = relpath(__file__, '../data/v.7/2009-04-23c - publications.csv')
#
#    # Delete all periodicals
#    Resource.objects.get_periodicals().delete()
#    
#    # Import periodicals
#    results = _import_resources(filename)
#    
#    return render(request, 'site_admin/import_resources.html', {
#        'page_title': 'Import Periodicals',
#        'page_time': time.time()-start,
#        'results': results,
#    })

#@login_required
#@transaction.commit_on_success
#def import_standards(request, source):
#    permissions.require_superuser(request)
#    
#    start = time.time()
#    
#    #filename = relpath(__file__, '../data/comsoc/standards.csv')
#    if source == 'v.7':
#        filename = relpath(__file__, '../data/v.7/2009-04-23b - standards.csv')
#    else:
#        raise Exception('Unknown source "%s".' % source)
#    
#    # Delete all standards
#    Resource.objects.get_standards().delete()
#    
#    # Import standards
#    results = _import_resources(filename)
#    
#    return render(request, 'site_admin/import_resources.html', {
#        'page_title': 'Import Standards',
#        'page_time': time.time()-start,
#        'results': results,
#    })

def _get_random_from_sequence(seq, num):
    results = []
    used_indexes = []
    seq_len = len(seq)
    while len(results) < num:
        i = random.randint(0, seq_len-1)
        if i not in used_indexes:
            results.append(seq[i])
            used_indexes.append(i)
    return results

@login_required
@admin_required
def fix_user_import(request):
    in_filename = relpath(__file__, '../data/v.7/2009-04-30 - users - append.csv')
    out_filename = relpath(__file__, '../data/v.7/2009-04-30 - users - append - fixed.csv')
    
    row_count = 0
    
    (in_file, reader) = _open_unicode_csv_reader(in_filename)
    out_file = codecs.open(out_filename, 'w', encoding='utf-8')

    # Write the header row
    out_row = '"%s","%s","%s","%s","%s","%s","%s"\r\n' % (
        'Username',
        'Password',
        'First Name',
        'Last Name',
        'Email',
        'Role',
        'Society Abbreviations',
    )
    out_file.write(out_row)
    
    row_count = 0
    generated_passwords = 0
    
    for row in reader:
        
        # Username,Password,First Name,Last Name,Email,Role,Society Abbreviations
        username, password, first_name, last_name, email, role, society_abbreviations = row
        
        # Generate a password if necessary
        if password.strip() == '':
            password = generate_password(chars='loweralphanumeric')
            generated_passwords += 1
        
        out_row = '%s,%s,%s,%s,%s,%s,%s\r\n' % (
            _escape_csv_field(username),
            _escape_csv_field(password),
            _escape_csv_field(first_name),
            _escape_csv_field(last_name),
            _escape_csv_field(email),
            _escape_csv_field(role),
            _escape_csv_field(society_abbreviations),
        )
        out_file.write(out_row)

        row_count += 1
            
    in_file.close()
    out_file.close()
    
    return render(request, 'site_admin/results.html', {
        'results': {
            'row_count': row_count,
            'generated_passwords': generated_passwords,
        }
    })
    
@login_required
@admin_required
@transaction.commit_manually
def import_users(request):
    if request.method == 'GET':
        # Display form
        form = ImportFileForm()
        return render(request, 'site_admin/import_users.html', {
            'form': form,
        })
        
    else:
        # Import users from uploaded file
        logging.debug('import_users()')
        
        file = request.FILES['file']
        
        row_count = 0
        users_created = 0
        society_managers_created = 0
        admins_created = 0
        errors = []
        imported_users = []
        users = []
        
        reader = _open_unicode_csv_reader_for_file(file)
        
        for row in reader:
            
            #Username,Password,First Name,Last Name,Email,Role,Society Abbreviations
            username, password, first_name, last_name, email, role, society_abbreviations = row
            
            username = username.strip()
            password = password.strip()
            first_name = first_name.strip()
            last_name = last_name.strip()
            email = email.strip()
            role = role.strip()
            society_abbreviations = society_abbreviations.strip()
            
            # DEBUG:
            if len(first_name) > 30:
                logging.warning('Imported user first_name is too long (>30 chars), "%s" truncated to "%s"' % (first_name, first_name[:30]))
                first_name = first_name[:30]
            
            if role not in Profile.ROLES:
                error.append('Unknown role "%s" for user "%s"' % (role, username))
            
            if username == '':
                errors.append('Username is blank.')
            
            if email == '':
                errors.append('Email is blank for user "%s"' % username)
            
            society_abbreviations = [society_abbreviation.strip() for society_abbreviation in _split_no_empty(society_abbreviations, ',')]
            
            societies = []
            for society_abbreviation in society_abbreviations:
                society = Society.objects.getFromAbbreviation(society_abbreviation)
                if society is None:
                    errors.append('Unknown society "%s" for user "%s"' % (society_abbreviation, username))
                else:
                    societies.append(society)
            
            if len(errors) == 0:
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=email,
                        password=password,
                    )
                except IntegrityError, e:
                    # Duplicate user error
                    errors.append('Failed to save user "%s", %s' % (username, e))
                else:
                    user.first_name = first_name
                    user.last_name = last_name
                    user.is_superuser = (role == Profile.ROLE_ADMIN)
                    user.is_staff = True
                    user.societies = societies
                    user.save()
                    
                    profile = user.get_profile()
                    profile.role = role
                    profile.save()
                    
                    # For sending login info later
                    user.plaintext_password = password
                    users.append(user)
                    
                    imported_users.append('"%s"' % username)
                    users_created += 1
                    if role == Profile.ROLE_ADMIN:
                        admins_created += 1
                    elif role == Profile.ROLE_SOCIETY_MANAGER:
                        society_managers_created += 1
            
            if not row_count % 10:
                logging.debug('  Reading row %d' % row_count)
                
            row_count += 1
                
        file.close()
        
        if len(errors) > 0:
            # Errors, rollback all changes & reset stats
            transaction.rollback()
        else:
            # Success, commit transaction
            transaction.commit()
        
        logging.debug('~import_users()')
        
        return render(request, 'site_admin/import_users.html', {
            'errors': list_to_html_list(errors, 'errors'),
            'users': users,
            'results': {
                'row_count': row_count,
                'users_created': users_created,
                'admins_created': admins_created,
                'society_managers_created': society_managers_created,
                'imported_users': list_to_html_list(imported_users),
            }
        })
    
@login_required
@admin_required
@transaction.commit_on_success
def import_resources(request):
    if request.method == 'GET':
        # Display form
        form = ImportFileForm()
        return render(request, 'site_admin/import_resources_file.html', {
            'form': form,
        })
        
    else:
        # Import resources from the uploaded file
        file = request.FILES['file']
        results = _import_resources(file)
        return render(request, 'site_admin/import_resources_file.html', {
            #'errors': list_to_html_list(errors, 'errors'),
            'results': results,
        })
    
@login_required
@admin_required
@transaction.commit_on_success
def import_clusters(request):
    if request.method == 'GET':
        # Display form
        form = ImportFileForm()
        return render(request, 'site_admin/import_file.html', {
            'page_title': 'Import Tag Clusters',
            'form': form,
        })
        
    else:
        
        # DEBUG: delete all clusters first
        #Node.objects.get_clusters().delete()
        
        # Import resources from the uploaded file
        file = request.FILES['file']
        results = _import_clusters(file)
        
        results['errors'] = list_to_html_list(results['errors'])
        
        return render(request, 'site_admin/import_file.html', {
            #'errors': list_to_html_list(errors, 'errors'),
            'page_title': 'Import Tag Clusters',
            'results': results,
        })

def _import_clusters(file):
    start = time.time()
    
    row_count = 0
    invalid_tags = 0
    tags_added = 0
    clusters_created = 0
    duplicate_clusters = 0
    errors = []
    
    reader = _open_unicode_csv_reader_for_file(file)
    
    for row in reader:
        
        # Cluster Name, Tag Names
        cluster_name, sector_name, tag_names = row
        
        # Formatting
        cluster_name = cluster_name.strip()
        sector_name = sector_name.strip()
        sector = Node.objects.get_sector_by_name(sector_name)
        tag_names = [tag_names.strip() for tag_names in tag_names.split('|')]
        tags = []
        for tag_name in tag_names:
            tag = Node.objects.get_tag_by_name(tag_name)
            if tag is None:
                errors.append('Unknown tag "%s"' % tag_name)
                invalid_tags += 1
            elif sector not in tag.parents.all():
                errors.append('Tag "%s" is not in the "%s" sector.' % (tag_name, sector_name))
            else:
                tags.append(tag)
                tags_added += 1
        
        if cluster_name == '':
            errors.append('Cluster name cannot be blank.')
        
        if len(errors) == 0:
            # Create the tag cluster
            if Node.objects.get_cluster_by_name(cluster_name, sector_name) is not None:
                # Duplicate cluster found
                errors.append('Duplicate cluster "%s" found in sector "%s".' % (cluster_name, sector_name))
                duplicate_clusters += 1
            else:
                cluster = Node.objects.create_cluster(cluster_name, sector)
                for tag in tags:
                    Node.objects.add_tag_to_cluster(cluster, tag)
                
                for tag in tags:
                    Node.objects.add_tag_to_cluster(cluster, tag)
                
                cluster.save()
                    
                clusters_created += 1
        
        if not row_count % 50:
            try:
                logging.debug('    Parsing row %d, row/sec %f' % (row_count, row_count/(time.time()-start) ))
            except Exception:
                pass
            
        row_count += 1
        
    file.close()
    
    return {
        'row_count': row_count,
        'invalid_tags': invalid_tags,
        'tags_added': tags_added,
        'clusters_created': clusters_created,
        'duplicate_clusters': duplicate_clusters,
        'errors': errors,
    }

@login_required
@admin_required
def list_sectors(request):
    sectors = Node.objects.getSectors()
    return render(request, 'site_admin/list_sectors.html', {
        'sectors': sectors,
    })

@login_required
@admin_required
def view_sector(request, sectorId):
    sector = Node.objects.get(id=sectorId)
    return render(request, 'site_admin/view_sector.html', {
        'sector': sector,
    })

@login_required
@admin_required
def list_orphan_tags(request):
    tags = Node.objects.get_orphan_tags()
    return render(request, 'site_admin/list_orphan_tags.html', {
        'tags': tags,
    })

@login_required
@admin_required
def send_email_all_users(request):
    if request.method == 'GET':
        form = SendEmailAllUsersForm(initial={
            'send_email': False,
            'body': """

IEEE Technology Navigator
%s""" % request.build_absolute_uri(reverse('index'))
        })
    else:
        form = SendEmailAllUsersForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data['send_email']:
                # Show preview of the email before sending
                vars = {}
                for name, value in request.POST.items():
                    vars[name] = value
                vars['send_email'] = u'on'
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']
                form = SendEmailAllUsersForm(vars)
                form.fields['subject'].widget = HiddenInput()
                form.fields['body'].widget = HiddenInput()
                return render(request, 'site_admin/send_email_all_users_preview.html', {
                    'form': form,
                    'subject': subject,
                    'body': body,
                })
            else:
                # Send the email
                user_emails = User.objects.all().values('email')
                user_emails = [obj['email'] for obj in user_emails]
                
                subject = form.cleaned_data['subject']
                body = form.cleaned_data['body']
                msg = EmailMessage(subject, body, to=[settings.SERVER_EMAIL], bcc=user_emails)
                msg.send()
                
                return HttpResponseRedirect(reverse('admin_send_email_all_users_confirmation'))
            
    return render(request, 'site_admin/send_email_all_users.html', {
        'form': form,
    })

@login_required
@admin_required
def send_email_all_users_confirmation(request):
    return render(request, 'site_admin/send_email_all_users_confirmation.html')

@login_required
@society_manager_or_admin_required
@transaction.commit_on_success
def edit_tags(request):
    # TODO: Check permissions on each tag
    assert request.method == 'POST'
    
    process_form = request.GET.get('process_form', None)
    return_url = request.GET.get('return_url')
    assert(return_url is not None)
    
    tag_ids = request.POST.getlist('tag_ids')
    tags = [Node.objects.get(id=tag_id) for tag_id in tag_ids]
    
    if process_form:
        # Process the form
        form = EditTagsForm(request.POST)
        
        if form.is_valid():
            
            for field_name in Filter.FILTERS:
                field_value = _parse_tristate_value(form.cleaned_data['%s_filter' % field_name])
                filter = Filter.objects.getFromValue(field_name)
                
                if field_value is True:
                    for tag in tags:
                        tag.filters.add(filter)
                        tag.save()
                elif field_value is False:
                    for tag in tags:
                        tag.filters.remove(filter)
                        tag.save()
            
            # Form saved successfully, redirect to previous page
            return HttpResponseRedirect(return_url)
    else:
        # Show the initial form
        form = EditTagsForm(initial={
            'emerging_technologies_filter': 'no change',
            'foundation_technologies_filter': 'no change',
            'hot_topics_filter': 'no change',
            'market_areas_filter': 'no change',
        })
    
    return render(request, 'site_admin/edit_tags.html', {
        'return_url': return_url,
        'form': form,
        'tags': tags,
    })

@login_required
@admin_required
def list_tags(request):
    tags = Node.objects.getTags()
    return render(request, 'site_admin/list_tags.html', {
        'page_title': 'List Tags',
        'tags': tags,
    })

@login_required
@admin_required
def view_tag(request, tag_id):
    try:
        tag = Node.objects.get(id=tag_id)
    except Node.DoesNotExist:
        # Return friendly error page about tag not existing
        return _tag_not_found_response(
            request,
            tag_id,
            None
        )
    return render(request, 'site_admin/view_tag.html', {
        'tag': tag,
    })

@login_required
@society_manager_or_admin_required
def create_tag(request):
    sector_id = request.GET.get('sector_id', None)
    done_action = request.GET.get('done_action', None)
    return_url = request.GET.get('return_url', '')
    if sector_id is None:
        sector = None
    else:
        sector = Node.objects.get(id=sector_id)
    society_id = request.GET.get('society_id', '')
    add_to_society = request.GET.get('add_to_society', '')
    default_tag_name = request.GET.get('default_tag_name', '')
    
    if request.method == 'GET':
        # Show the create tag form
        form = CreateTagForm(initial={
            'sector': sector_id,
            'name': default_tag_name,
        })
        
        if request.is_ajax():
            form.fields['related_tags'].widget.set_show_create_tag_link(False)
        
        if society_id != '':
            form.fields['related_tags'].widget.set_society_id(society_id)
        
    else:
        # Process the form
        form = CreateTagForm(request.POST)
        
        if request.is_ajax():
            form.fields['related_tags'].widget.set_show_create_tag_link(False)
            
        if society_id != '':
            form.fields['related_tags'].widget.set_society_id(society_id)
            
        if form.is_valid():
            tag = Node.objects.create(
                name=form.cleaned_data['name'],
                node_type=NodeType.objects.getFromName(NodeType.TAG),
            )
            tag.parents=form.cleaned_data['sectors']
            
            # Don't add society if "add_to_society" is 0
            if society_id != '' and add_to_society != '0':
                society = Society.objects.get(id=int(society_id))
                tag.societies = [society]
            
            tag.filters = form.cleaned_data['filters']
            tag.related_tags = form.cleaned_data['related_tags']
            tag.save()
            
            if return_url != '':
                return HttpResponseRedirect(return_url)
            
            elif request.is_ajax():
                return HttpResponse('ajax\n' + json.dumps({
                    'event': 'created_tag',
                    'data': {
                        'tag': {
                            'name': tag.name,
                            'name_link': reverse('admin_edit_tag', args=[tag.id]) + '?return_url=%s' % quote('/admin/?hash=' + quote('#tab-tags-tab')),
                            'value': tag.id,
                            'tag_name': tag.name,
                            'sector_names': tag.sector_names(),
                            'num_societies': tag.societies.count(),
                            'num_related_tags': tag.related_tags.count(),
                            'num_filters': tag.filters.count(),
                            'num_resources': tag.resources.count(),
                        },
                    },
                }))
                
            else:
                # TODO: This is out of date, remove it
                assert False, 'This code path is obsolete.'
                #return HttpResponse("""
                #    <script>
                #        if (opener && opener.notify) {
                #            opener.notify('created_tag', %s);
                #        }
                #        window.close();
                #    </script>
                #    <a href="javascript:window.close();">Close window</a>
                #    """
                #    % json.dumps({
                #        'tag': {
                #            'id': tag.id,
                #            'name': tag.name,
                #            'sector_name': tag.parent.name,
                #            'name_with_sector': tag.name_with_sector(),
                #        }
                #    })
                #)
        #return HttpResponseRedirect(reverse('admin_view_tag', args=(tagId,)))
            
    return render(request, 'site_admin/create_tag.html', {
        'form': form,
        'sector': sector,
        'society_id': society_id,
        'add_to_society': add_to_society,
        'done_action': done_action,
        'return_url': return_url,
    })

@login_required
@society_manager_or_admin_required
def edit_tag(request, tag_id):
    "Edit an existing tag."
    return_url = request.GET.get('return_url', '')
    society_id = request.GET.get('society_id', '')
    try:
        tag = Node.objects.get(id=tag_id)
    except Node.DoesNotExist:
        # Return friendly error page about tag not existing
        return _tag_not_found_response(
            request,
            tag_id,
            return_url
        )
    
    form = EditTagForm(initial={
        'id': tag.id,
        'name': tag.name,
        'parents': [parent.id for parent in tag.parents.all()],
        'node_type': tag.node_type.id,
        'societies': tag.societies.all(),
        'filters': [filter.id for filter in tag.filters.all()],
        'related_tags': tag.related_tags.all(),
    })
    
    form.fields['related_tags'].widget.set_exclude_tag_id(tag.id)
    if society_id != '':
        form.fields['related_tags'].widget.set_society_id(int(society_id))
    
    if request.user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
        # Disable certain fields for the society managers
        make_display_only(form.fields['societies'], model=Society, is_multi_search=True)
        sector_ids = [str(sector.id) for sector in tag.parents.all()]
        #form.fields['related_tags'].widget.set_search_url(reverse('ajax_search_tags') + '?filter_sector_ids=' + ','.join(sector_ids))
    
    num_filters = tag.filters.count()
        
    return render(request, 'site_admin/edit_tag.html', {
        'tag': tag,
        'form': form,
        'return_url': return_url,
        'society_id': society_id,
        'num_filters': num_filters,
    })
        
@login_required
@society_manager_or_admin_required
def save_tag(request, tag_id):
    "Saves an existing tag."
    return_url = request.GET.get('return_url', '')
    society_id = request.GET.get('society_id', '')
    tag = Node.objects.get(id=tag_id)
    
    form = EditTagForm(request.POST)
    if not form.is_valid():
        
        # Form had errors, re-render
        form.fields['related_tags'].widget.set_exclude_tag_id(tag.id)
        if society_id != '':
            form.fields['related_tags'].widget.set_society_id(int(society_id))
            
        if request.user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
            # Disable certain fields for the society managers
            make_display_only(form.fields['societies'], model=Society, is_multi_search=True)
            tag_id = int(request.POST['id'])
            tag = Node.objects.get(id=tag_id)
            sector_ids = [str(sector.id) for sector in tag.parents.all()]
            #form.fields['related_tags'].widget.set_search_url(reverse('ajax_search_tags') + '?filter_sector_ids=' + ','.join(sector_ids))
            
        return render(request, 'site_admin/edit_tag.html', {
            'tag': tag,
            'form': form,
            'return_url': return_url,
            'society_id': society_id,
        })
        
    else:
        
        # Form is valid, save it
        if form.cleaned_data['id'] is None:
            tag = Node.objects.create()
        else:
            tag = Node.objects.get(id=form.cleaned_data['id'])
        
        tag.name = form.cleaned_data['name']
        
        # Remove all unselected sectors
        for sector in tag.get_sectors():
            if sector not in form.cleaned_data['parents']:
                tag.parents.remove(sector)
                logging.debug('Removing sector "%s"' % sector.name)
        
        # Add all selected sectors
        for sector in form.cleaned_data['parents']:
            if sector not in tag.parents.all():
                tag.parents.add(sector)
                logging.debug('Adding sector "%s"' % sector.name)
        
        #tag.node_type = form.cleaned_data['node_type']
        if form.cleaned_data['societies'] is not None:
            tag.societies = form.cleaned_data['societies']
        tag.filters = form.cleaned_data['filters']
        tag.related_tags = form.cleaned_data['related_tags']
        tag.save()
        
        clusters = tag.get_parent_clusters()
        for cluster in clusters:
            cluster.cluster_update_filters()
        
        if return_url != '':
            return HttpResponseRedirect(return_url)
        else:
            return HttpResponseRedirect(reverse('admin_view_tag', args=[tag.id]))

def _tag_not_found_response(request, tag_id, return_url):
    if return_url is None:
        return_url = 'javascript:history.back();'
    return render(request, 'error_tag_not_found.html', {
        'tag_id': tag_id,
        'return_url': return_url,
    })

@login_required
@admin_required
def delete_tag(request, tag_id):
    return_url = request.GET.get('return_url')
    
    try:
        tag = Node.objects.get(id=tag_id)
    except Node.DoesNotExist, e:
        # Return friendly error page about tag not existing
        return _tag_not_found_response(
            request,
            tag_id,
            return_url
        )
        
    assert tag.node_type.name == NodeType.TAG
    tag.delete()
    
    if return_url is not None:
        return HttpResponseRedirect(return_url)
    else:
        return HttpResponseRedirect(reverse('admin_home'))

def _combine_tags(tag_id1, tag_id2):
    """
    Combines two tags into one, merging all tag data:
        -parent sectors
        -societies
        -filters
        -related tags
        -resources
    Deletes the tag with the higher ID, preserves the tag with the lower ID.
    """
    tag_id1 = int(tag_id1)
    tag_id2 = int(tag_id2)
    
    #logging.debug('tag_id1: %s' % tag_id1)
    #logging.debug('tag_id2: %s' % tag_id2)
    
    # Ensure that tag_id1 is the lower of the two.  This is the one we want to keep.
    if tag_id1 > tag_id2:
        tag_id1, tag_id2 = tag_id2, tag_id1
    
    #logging.debug('tag_id1: %s' % tag_id1)
    #logging.debug('tag_id2: %s' % tag_id2)
    
    tag1 = Node.objects.get(id=tag_id1)
    assert tag1.node_type.name == NodeType.TAG
    
    tag2 = Node.objects.get(id=tag_id2)
    assert tag2.node_type.name == NodeType.TAG
    
    #logging.debug('tag1.name: %s' % tag1.name)
    #logging.debug('tag1.id: %s' % tag1.id)
    #logging.debug('tag2.name: %s' % tag2.name)
    #logging.debug('tag2.id: %s' % tag2.id)
    #logging.debug('')
    
    # Add all parents from tag2 to tag1
    #logging.debug('tag1.parents: %r' % tag1.parents.all())
    #logging.debug('tag2.parents: %r' % tag2.parents.all())
    for parent in tag2.parents.all():
        if tag1.parents.filter(id=parent.id).count() == 0:
            tag1.parents.add(parent)
    #logging.debug('----------')
    #logging.debug('tag1.parents: %r' % tag1.parents.all())
    #logging.debug('tag2.parents: %r' % tag2.parents.all())
    #logging.debug('')
    
    # Add all societies from tag2 to tag1
    #logging.debug('tag1.societies: %r' % tag1.societies.all())
    #logging.debug('tag2.societies: %r' % tag2.societies.all())
    for society in tag2.societies.all():
        if tag1.societies.filter(id=society.id).count() == 0:
            tag1.societies.add(society)
    #logging.debug('----------')
    #logging.debug('tag1.societies: %r' % tag1.societies.all())
    #logging.debug('tag2.societies: %r' % tag2.societies.all())
    #logging.debug('')
    
    # Add all filters from tag2 to tag1
    #logging.debug('tag1.filters: %r' % tag1.filters.all())
    #logging.debug('tag2.filters: %r' % tag2.filters.all())
    for filter in tag2.filters.all():
        if tag1.filters.filter(id=filter.id).count() == 0:
            tag1.filters.add(filter)
    #logging.debug('----------')
    #logging.debug('tag1.filters: %r' % tag1.filters.all())
    #logging.debug('tag2.filters: %r' % tag2.filters.all())
    #logging.debug('')
    
    # Add all related_tags from tag2 to tag1
    #logging.debug('tag1.related_tags: %r' % tag1.related_tags.all())
    #logging.debug('tag2.related_tags: %r' % tag2.related_tags.all())
    for related_tag in tag2.related_tags.all():
        # NOTE: Make sure that tag1 doesn't end up with itself as a related tag
        if tag1.related_tags.filter(id=related_tag.id).count() == 0 and tag1 != related_tag:
            tag1.related_tags.add(related_tag)
    #logging.debug('----------')
    #logging.debug('tag1.related_tags: %r' % tag1.related_tags.all())
    #logging.debug('tag2.related_tags: %r' % tag2.related_tags.all())
    #logging.debug('')
    
    # Add all resources from tag2 to tag1
    #logging.debug('tag1.resources: %r' % tag1.resources.all())
    #logging.debug('tag2.resources: %r' % tag2.resources.all())
    for resource in tag2.resources.all():
        if tag1.resources.filter(id=resource.id).count() == 0:
            tag1.resources.add(resource)
    #logging.debug('----------')
    #logging.debug('tag1.resources: %r' % tag1.resources.all())
    #logging.debug('tag2.resources: %r' % tag2.resources.all())
    #logging.debug('')
    
    tag1.save()
    tag2.delete()
    
    return tag1
    
@login_required
@admin_required
@transaction.commit_on_success
def combine_tags(request):
    return_url = request.GET['return_url']
    duplicate_tags_json = request.POST['duplicate_tags_json']
    
    duplicate_tags = json.loads(duplicate_tags_json)
    
    for duplicate_tag in duplicate_tags:
        try:
            _combine_tags(duplicate_tag[1], duplicate_tag[2])
        except Node.DoesNotExist, e:
            logging.debug('Tag does not exist: %s' % e)
    
    return HttpResponseRedirect(return_url)

@login_required
@admin_required
def view_cluster(request, cluster_id):
    cluster = Node.objects.get(id=cluster_id)
    return render(request, 'site_admin/view_cluster.html', {
        'cluster': cluster,
    })

@login_required
@admin_required
@transaction.commit_on_success
def edit_cluster(request, cluster_id=None):
    if cluster_id is not None:
        cluster = Node.objects.get(id=cluster_id)
        sector_id = cluster.get_sector().id
    else:
        cluster = None
        sector_id = request.GET.get('sector_id')
    
    if request.method == 'GET':
        # Show the form
        if cluster is None:
            if sector_id is None:
                # Show 'Choose a sector' page
                sectors = Node.objects.getSectors()
                return render(request, 'site_admin/create_cluster_select_sector.html', {
                    'sectors': sectors,
                })
            else:
                # New cluster
                sector = Node.objects.get(id=sector_id)
                assert sector.node_type.name == NodeType.SECTOR, 'Node "%s" is not a sector' % sector.name
                form = EditClusterForm(initial={
                    #'sector': sector,
                    'sector': sector_id,
                })
                
        else:
            # Existing cluster
            tags = cluster.get_tags()
            form = EditClusterForm(instance=cluster, initial={
                'tags': tags,
                'sector': cluster.get_sector().id,
            })
    else:
        # Process the form
        form = EditClusterForm(request.POST, instance=cluster)
        if form.is_valid():
            if cluster is not None:
                # Updating an existing cluster
                form.save()
            else:
                # Saving a new cluster
                cluster = form.save(commit=False)
                cluster.node_type = NodeType.objects.getFromName(NodeType.TAG_CLUSTER)
                cluster.save()
                cluster.parents.add(form.cleaned_data['sector'])
            
            tags = form.cleaned_data['tags']
            
            # First remove all existing tags
            for tag in cluster.get_tags():
                if tag not in tags:
                    Node.objects.remove_tag_from_cluster(cluster, tag)
                    
            # Now add any new tags
            for tag in tags:
                if tag not in cluster.get_tags():
                    Node.objects.add_tag_to_cluster(cluster, tag)
                    
            return HttpResponseRedirect(reverse('admin_view_cluster', args=[cluster.id]))
        
    # Limit tags to the selected sector
    form.fields['tags'].widget.set_search_url(reverse('ajax_search_tags') + '?filter_sector_ids=%s' % sector_id)
        
    return render(request, 'site_admin/edit_cluster.html', {
        'cluster': cluster,
        'form': form,
    })

@login_required
@admin_required
def delete_cluster(request, cluster_id):
    #return_to = request.GET.get('return_to')
    cluster = Node.objects.get(id=cluster_id)
    cluster.delete()
    #return HttpResponseRedirect(return_to)
    return HttpResponseRedirect(reverse('admin_clusters_report'))
    
@login_required
@admin_required
def search_tags(request):
    tag_results = None
    if request.method == 'GET':
        form = SearchTagsForm()
    else:
        form = SearchTagsForm(request.POST)
        if form.is_valid():
            tag_name = form.cleaned_data['tag_name']
            tag_results = Node.objects.searchTagsByNameSubstring(tag_name)
    
    return render(request, 'site_admin/search_tags.html', {
        'form': form,
        'tag_results': tag_results,
    })

@login_required
@admin_required
def users(request):
    users = User.objects.all()
    return render(request, 'site_admin/users.html', {
        'users': users,
    })

@login_required
@admin_required
def view_user(request, user_id):
    user = User.objects.get(id=user_id)
    return render(request, 'site_admin/view_user.html', {
        'view_user': user,
    })
    
@login_required
@admin_required
def edit_user(request, user_id=None):
    if user_id is None:
        # creating a new user
        form = UserForm(initial={
            'role': Profile.ROLE_SOCIETY_MANAGER,
        })
    else:
        # editing an existing user
        user = User.objects.get(id=user_id)
        form = UserForm(initial={
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'role': user.get_profile().role,
            'societies': [society.id for society in user.societies.all()],
        })
    return render(request, 'site_admin/edit_user.html', {
        'user_id': user_id,
        'form': form,
    })

def _errors_to_list(errors):
    if len(errors) == 0:
        return None
    else:
        result = '<ul class="error">\n'
        for error in errors:
            result += '<li>%s</li>\n' % error
        result += '</ul>\n'
        return result

@login_required
@admin_required
def save_user(request):
    user_id = request.POST.get('id', None)
    form = UserForm(request.POST)
    errors = []
    
    if form.is_valid():
        # Prevent duplicate usernames
        if form.cleaned_data['id'] is None:
            # New user
            if User.objects.filter(username=form.cleaned_data['username']).count() > 0:
                errors.append('The username "%s" already exists in the system.' % form.cleaned_data['username'])
        else:
            # Existing user, check against *other* users
            if User.objects.filter(username=form.cleaned_data['username']).exclude(id=form.cleaned_data['id']).count() > 0:
                errors.append('The username "%s" already exists in the system.' % form.cleaned_data['username'])
        
        # Prevent duplicate emails
        if form.cleaned_data['id'] is None:
            # New user
            if User.objects.filter(email=form.cleaned_data['email']).count() > 0:
                errors.append('The email "%s" already exists in the system.' % form.cleaned_data['email'])
        else:
            # Existing user, check against *other* users
            if User.objects.filter(email=form.cleaned_data['email']).exclude(id=form.cleaned_data['id']).count() > 0:
                errors.append('The email "%s" already exists in the system.' % form.cleaned_data['email'])
        
        # Validate password
        if form.cleaned_data['id'] is None and form.cleaned_data['password1'] == '' and form.cleaned_data['password2'] == '':
            errors.append('Please enter a password.')
        elif form.cleaned_data['password1'] != form.cleaned_data['password2']:
            errors.append('The passwords did not match.')
        
        if len(errors) == 0:
            # Form is valid
            if form.cleaned_data['id'] is None:
                # Creating user
                user = User.objects.create(
                    username = form.cleaned_data['username'],
                    email = form.cleaned_data['email'],
                    password = form.cleaned_data['password1'],
                )
            else:
                user = User.objects.get(id=form.cleaned_data['id'])
                user.username = form.cleaned_data['username']
                user.email = form.cleaned_data['email']
            
            if form.cleaned_data['password1'] != '':
                user.set_password(form.cleaned_data['password1'])
                ask_send_login_info = True
            else:
                ask_send_login_info = False
            
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            
            if form.cleaned_data['role'] == Profile.ROLE_ADMIN:
                user.is_superuser = True
                user.is_staff = True
            elif form.cleaned_data['role'] == Profile.ROLE_SOCIETY_ADMIN:
                user.is_superuser = False
                user.is_staff = True
            elif form.cleaned_data['role'] == Profile.ROLE_SOCIETY_MANAGER:
                user.is_superuser = False
                user.is_staff = True
            elif form.cleaned_data['role'] == Profile.ROLE_END_USER:
                user.is_superuser = False
                user.is_staff = False
            else:
                raise Exception('Unknown role "%s"' % form.cleaned_data['role'])
            
            user.societies = form.cleaned_data['societies']
            user.save()
            
            profile = user.get_profile()
            profile.role = form.cleaned_data['role']
            profile.save()
            
            if ask_send_login_info:
                return render(request, 'site_admin/ask_send_login_info.html', {
                    'edited_user': user,
                    'plaintext_password': form.cleaned_data['password1'],
                })
                
            return HttpResponseRedirect(reverse('admin_users'))
        
    return render(request, 'site_admin/edit_user.html', {
        'user_id': user_id,
        'errors': _errors_to_list(errors),
        'form': form,
    })

@login_required
@admin_required
def delete_user(request, user_id):
    "Deletes a user."
    User.objects.get(id=user_id).delete()
    return HttpResponseRedirect(reverse('admin_users'))

@login_required
@admin_required
def delete_users(request):
    """Delete a list of users.
Takes as input a list of user id's in the POST list 'user_ids' (use checkboxes with name="user_ids").
"""
    user_ids = request.POST.getlist('user_ids')
    for user_id in user_ids:
        User.objects.get(id=user_id).delete()
        
    return HttpResponseRedirect(reverse('admin_users'))

def _send_user_login_info_email(request, user, plaintext_password, reason):
    
    if reason == 'created':
        text1 = 'Your account has been created'
    elif reason == 'password_changed':
        text1 = 'Your account\'s password has been changed'
    else:
        raise Exception('Unknown reason "%s"' % reason)
    
    abs_index_url = request.build_absolute_uri(reverse('index'))
    abs_login_url = request.build_absolute_uri(reverse('admin_login'))
    
    subject = 'Your login information for %s' % abs_index_url
    message = """%s on %s.  Here is your login information:

Username: %s
Password: %s

To login to your account, click click on this link and enter your login information from above:
%s
""" % (
        text1,
        abs_index_url,
        user.username,
        plaintext_password,
        abs_login_url,
    )
    
    logging.debug('Sending login info email to %s:\nsubject: %s\nmessage: %s\n' % (
        user.email,
        subject,
        message,
    ))
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
    
@login_required
@admin_required
def send_login_info(request, reason):
    user_ids = request.POST.getlist('user_ids')
    plaintext_passwords = request.POST.getlist('plaintext_passwords')
    
    for user_id, plaintext_password in zip(user_ids, plaintext_passwords):
        user = User.objects.get(id=user_id)
        _send_user_login_info_email(request, user, plaintext_password, reason)
    
    return HttpResponseRedirect(reverse('admin_users'))

@login_required
@society_manager_or_admin_required
def societies(request):
    societies = Society.objects.getForUser(request.user)
    return render(request, 'site_admin/societies.html', {
        'societies': societies,
    })

@login_required
@admin_required
def view_society(request, society_id):
    society = Society.objects.get(id=society_id)
    return render(request, 'site_admin/view_society.html', {
        'society': society,
    })

def _get_paged_tags(items_per_page, society, tag_sort, tag_page):
    assert type(items_per_page) is int
    assert type(tag_page) is int
    
    if tag_sort == 'name_ascending':
        tags = society.tags.order_by('name')
    elif tag_sort == 'name_descending':
        tags = society.tags.order_by('-name')
    
    elif tag_sort == 'sector_list_ascending':
        tags = society.tags.extra(select={
            'sectors_list': """
                SELECT GROUP_CONCAT(sectors.name ORDER BY sectors.name SEPARATOR ', ')
                FROM ieeetags_node_parents INNER JOIN ieeetags_node AS sectors
                ON ieeetags_node_parents.to_node_id = sectors.id
                WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id
                GROUP BY ieeetags_node_parents.from_node_id
            """,
        }, order_by=[
            'sectors_list',
        ])
    elif tag_sort == 'sector_list_descending':
        tags = society.tags.extra(select={
            'sectors_list': """
                SELECT GROUP_CONCAT(sectors.name ORDER BY sectors.name SEPARATOR ', ')
                FROM ieeetags_node_parents INNER JOIN ieeetags_node AS sectors
                ON ieeetags_node_parents.to_node_id = sectors.id
                WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id
                GROUP BY ieeetags_node_parents.from_node_id
            """,
        }, order_by=[
            '-sectors_list',
        ])
    
    elif tag_sort == 'num_societies_ascending':
        tags = society.tags.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_node_societies.id) FROM ieeetags_node_societies WHERE ieeetags_node_societies.node_id = ieeetags_node.id',
        }, order_by=[
            'num_societies',
        ])
    elif tag_sort == 'num_societies_descending':
        tags = society.tags.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_node_societies.id) FROM ieeetags_node_societies WHERE ieeetags_node_societies.node_id = ieeetags_node.id',
        }, order_by=[
            '-num_societies',
        ])
    
    elif tag_sort == 'num_filters_ascending':
        tags = society.tags.extra(select={
            'num_filters': 'SELECT COUNT(ieeetags_node_filters.id) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id',
        }, order_by=[
            'num_filters',
        ])
    elif tag_sort == 'num_filters_descending':
        tags = society.tags.extra(select={
            'num_filters': 'SELECT COUNT(ieeetags_node_filters.id) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id',
        }, order_by=[
            '-num_filters',
        ])
    
    elif tag_sort == 'num_resources_ascending':
        tags = society.tags.extra(select={
            'num_resources1': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id',
        }, order_by=[
            'num_resources1',
        ])
    elif tag_sort == 'num_resources_descending':
        tags = society.tags.extra(select={
            'num_resources1': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id',
        }, order_by=[
            '-num_resources1',
        ])
    
    elif tag_sort == 'num_related_tags_ascending':
        tags = society.tags.extra(select={
            'num_related_tags1': 'SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id',
        }, order_by=[
            'num_related_tags1',
        ])
    elif tag_sort == 'num_related_tags_descending':
        tags = society.tags.extra(select={
            'num_related_tags1': 'SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id',
        }, order_by=[
            '-num_related_tags1',
        ])
    
    else:
        raise Exception('Unknown tag_sort "%s"' % tag_sort)
    
    num_tags = tags.count()
    num_tag_pages = int(math.ceil(num_tags / float(items_per_page)))
    
    tag_start_count = (tag_page-1) * items_per_page
    tag_end_count = (tag_page) * items_per_page
    tags = tags[tag_start_count:tag_end_count]
    
    return (tags, num_tag_pages)

@login_required
@society_manager_or_admin_required
def manage_society(request, society_id):
    try:
        permissions.require_society_user(request, society_id)
    except Exception, e:
        # Give a friendly error page with a link to the correct home page
        # TODO: Better fix for this later
        return permission_denied(request)
    
    items_per_page = int(request.GET.get('items_per_page', 50))
    
    items_per_page_form = ItemsPerPageForm(initial={
        'items_per_page': items_per_page,
    })
    
    resource_filter = request.GET.get('resource_filter', '').strip()
    
    # Default to name/ascending resource_sort
    resource_sort = request.GET.get('resource_sort', 'priority_ascending')
    resource_page = int(request.GET.get('resource_page', 1))
    
    # Default to name/ascending tag_sort
    tag_sort = request.GET.get('tag_sort', 'name_ascending')
    tag_page = int(request.GET.get('tag_page', 1))
    
    society = Society.objects.get(id=society_id)
    
    resources1 = society.resources
    num_unfiltered_resources = resources1.count()
    
    if resource_filter != '':
        keywords = resource_filter.split(' ')
        for keyword in keywords:
            resources1 = resources1.filter(name__icontains=keyword)
    
    form = ManageSocietyForm(initial={
        'tags': society.tags.all(),
    })
    
    form.fields['tags'].widget.set_society_id(society_id)
    
    if resource_sort == 'name_ascending':
        resources1 = resources1.order_by('name')
    elif resource_sort == 'name_descending':
        resources1 = resources1.order_by('-name')
    
    elif resource_sort == 'ieee_id_ascending':
        
        # Ignore warning about turning non-numeric value into an integer ("Truncated incorrect INTEGER value: 'xxxx'")
        warnings.filterwarnings('ignore', '^Truncated incorrect INTEGER value:.+')
        
        resources1 = resources1.extra(select={
            'ieee_id_num': 'SELECT CAST(ieee_id AS SIGNED INTEGER)',
        }, order_by=[
            'ieee_id_num',
            'ieee_id',
            'name',
        ])
        
    elif resource_sort == 'ieee_id_descending':
        
        # Ignore warning about turning non-numeric value into an integer ("Truncated incorrect INTEGER value: 'xxxx'")
        warnings.filterwarnings('ignore', '^Truncated incorrect INTEGER value:.+')
        
        resources1 = resources1.extra(select={
            'ieee_id_num': 'SELECT CAST(ieee_id AS SIGNED INTEGER)',
        }, order_by=[
            '-ieee_id_num',
            '-ieee_id',
            '-name',
        ])
    
    elif resource_sort == 'resource_type_ascending':
        resources1 = resources1.order_by('resource_type', 'standard_status', 'name')
    elif resource_sort == 'resource_type_descending':
        resources1 = resources1.order_by('-resource_type', '-standard_status', '-name')
    
    elif resource_sort == 'url_ascending':
        resources1 = resources1.order_by('url', 'name')
    elif resource_sort == 'url_descending':
        resources1 = resources1.order_by('-url', '-name')
    
    elif resource_sort == 'num_tags_ascending':
        resources1 = resources1.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_tags',
        ])
    elif resource_sort == 'num_tags_descending':
        resources1 = resources1.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_tags',
        ])
    
    elif resource_sort == 'num_societies_ascending':
        resources1 = resources1.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_societies',
        ])
    elif resource_sort == 'num_societies_descending':
        resources1 = resources1.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_societies',
        ])
    
    # NOTE: These are reversed, since that seems more intutive
    elif resource_sort == 'priority_ascending':
        resources1 = resources1.order_by('-priority_to_tag', 'completed', 'name')
    elif resource_sort == 'priority_descending':
        resources1 = resources1.order_by('priority_to_tag', '-completed', '-name')
    
    elif resource_sort == 'completed_ascending':
        resources1 = resources1.order_by('-completed', '-priority_to_tag', 'name')
    elif resource_sort == 'completed_descending':
        resources1 = resources1.order_by('completed', 'priority_to_tag', '-name')
    
    elif resource_sort == 'description_ascending':
        resources1 = resources1.order_by('description', 'name')
    elif resource_sort == 'description_descending':
        resources1 = resources1.order_by('-description', '-name')
    
    else:
        raise Exception('Unknown resource_sort "%s"' % resource_sort)
        
    resources1 = list(resources1)
    resources1 = group_conferences_by_series(resources1, True)
    
    # Limit search results to one page
    num_resources = len(resources1)
    num_resource_pages = int(math.ceil(num_resources / float(items_per_page)))
    
    # NOTE: resource_page starts at 1, not 0
    resource_start_count = (resource_page-1) * items_per_page
    resource_end_count = (resource_page) * items_per_page
    
    resources1 = resources1[resource_start_count:resource_end_count]
    resource_page_url = reverse('admin_manage_society', args=[society.id]) + '?resource_sort=' + quote(resource_sort) + '&amp;resource_filter=' + quote(resource_filter) + '&amp;resource_filter=' + quote(resource_filter) + '&amp;items_per_page=' + quote(str(items_per_page)) + '&amp;resource_page={{ page }}#tab-resources-tab'
    
    (tags, num_tag_pages) = _get_paged_tags(items_per_page, society, tag_sort, tag_page)
    tag_page_url = reverse('admin_manage_society', args=[society.id]) + '?tag_sort=' + quote(tag_sort) + '&amp;items_per_page=' + quote(str(items_per_page)) + '&amp;tag_page={{ page }}#tab-tags-tab'
    
    # For each resource, get a list of society abbreviations in alphabetical order
    for i in range(len(resources1)):
        resources1[i].society_abbreviations = [society1.abbreviation for society1 in resources1[i].societies.order_by('abbreviation')]
        
        if resources1[i].priority_to_tag and resources1[i].completed:
            resources1[i].classes = 'resource-completed-priority'
        elif resources1[i].priority_to_tag:
            resources1[i].classes = 'resource-priority'
        elif resources1[i].completed:
            resources1[i].classes = 'resource-completed'
        else:
            resources1[i].classes = ''
        
        if resources1[i].conference_series != '' and resources1[i].is_current_conference:
            resources1[i].classes += ' current-conference current-conference-%s { id:%s }' % (resources1[i].id, resources1[i].id)

    resources = resources1
    
    tags_tab_url = reverse('admin_manage_society', args=[society_id]) + '#tab-tags-tab'
    
    return render(request, 'site_admin/manage_society.html', {
        'society': society,
        'form': form,
        'resource_filter': resource_filter,
        
        'resources': resources,
        'resource_sort': resource_sort,
        'resource_page': resource_page,
        'num_resources': num_resources,
        'num_unfiltered_resources': num_unfiltered_resources,
        'resource_page_url': resource_page_url,
        'num_resource_pages': num_resource_pages,
        
        'tags': tags,
        'tags_tab_url': tags_tab_url,
        'tag_sort': tag_sort,
        'tag_page': tag_page,
        'num_tag_pages': num_tag_pages,
        'tag_page_url': tag_page_url,
        
        'return_url': request.get_full_path(),
        'items_per_page': items_per_page,
        'items_per_page_form': items_per_page_form,
        
        'DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB': settings.DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB,
    })

@login_required
@society_manager_or_admin_required
def manage_society_tags_table(request, society_id, tag_sort, tag_page, items_per_page):
    society = Society.objects.get(id=society_id)
    tag_page = int(tag_page)
    items_per_page = int(items_per_page)
    (tags, num_tag_pages) = _get_paged_tags(items_per_page, society, tag_sort, tag_page)
    tag_page_url = reverse('admin_manage_society', args=[society.id]) + '?tag_sort=' + quote(tag_sort) + '&amp;items_per_page=' + quote(str(items_per_page)) + '&amp;tag_page={{ page }}#tab-tags-tab'

    return_url = reverse('admin_manage_society', args=[society.id]) + '?' + urlencode({
        'tag_sort':tag_sort,
        'tag_page':tag_page,
    })
    
    items_per_page_form = ItemsPerPageForm(initial={
        'items_per_page': items_per_page,
    })
    
    return render(request, 'site_admin/manage_society_tags_table.html', {
        'tag_sort': tag_sort,
        'tag_page': tag_page,
        'num_tag_pages': num_tag_pages,
        'society': society,
        'tags': tags,
        'tag_page_url': tag_page_url,
        'return_url': return_url,
        'items_per_page': items_per_page,
        'items_per_page_form': items_per_page_form,
    })

@login_required
@admin_required
def edit_society(request, society_id=None):
    return_url = request.GET.get('return_url', '')
    if society_id is None:
        # creating a new society
        society = None
        form = SocietyForm()
    else:
        # editing an existing society
        society = Society.objects.get(id=society_id)
        if not Permission.objects.user_can_edit_society(request.user, society):
            raise Exception('User does not have permission to edit the society')
    
        form = SocietyForm(initial={
            'id': society.id,
            'name': society.name,
            'abbreviation': society.abbreviation,
            'url': society.url,
            'users': [user.id for user in society.users.all()],
            'tags': society.tags.all(),
            'resources': society.resources.all(),
        })
        
        if not Permission.objects.user_can_edit_society_name(request.user, society):
            # Only superuser has edit permissions for the name/abbreviation
            make_display_only(form.fields['name'])
            make_display_only(form.fields['abbreviation'])
            make_display_only(form.fields['users'], model=User)
        
    return render(request, 'site_admin/edit_society.html', {
        'society': society,
        'form': form,
        'return_url': return_url,
    })
        
@login_required
@admin_required
def save_society(request):
    return_url = request.GET.get('return_url', '')
    form = SocietyForm(request.POST)
    if not form.is_valid():
        
        if request.POST['id'] is not None and request.POST['id'] != '':
            society = Society.objects.get(id=int(request.POST['id']))
        else:
            society = None
        
        return render(request, 'site_admin/edit_society.html', {
            'society': society,
            'form': form,
            'return_url': return_url,
        })
    else:
        if form.cleaned_data['id'] is None:
            society = Society.objects.create()
        else:
            society = Society.objects.get(id=form.cleaned_data['id'])
        
        society.name = form.cleaned_data['name']
        society.abbreviation = form.cleaned_data['abbreviation']
        society.url = form.cleaned_data['url']
        society.users = form.cleaned_data['users']
        
        # Society does not need to edit tags/resources in this form
        if request.user.is_superuser:
            society.tags = form.cleaned_data['tags']
            society.resources = form.cleaned_data['resources']
        society.save()
        
        #print 'return_url:', return_url
        #print 'society:', society
        #print 'society.id:', society.id
        #print "reverse('admin_view_society', args=[society.id]):", reverse('admin_view_society', args=[society.id])
        url = reverse('admin_view_society', args=[society.id])
        #print 'url:', url
        
        if return_url != '':
            return HttpResponseRedirect(return_url)
        else:
            #return HttpResponseRedirect(reverse('admin_view_society', args=[society.id]))
            return HttpResponseRedirect(url)

@login_required
@admin_required
def delete_society(request, society_id):
    Society.objects.get(id=society_id).delete()
    return HttpResponseRedirect(reverse('admin_societies'))

@login_required
@admin_required
def search_societies(request):
    society_results = None
    if request.method == 'GET':
        form = SearchSocietiesForm()
    else:
        form = SearchSocietiesForm(request.POST)
        if form.is_valid():
            society_name = form.cleaned_data['society_name']
            society_results = Society.objects.searchByNameSubstring(society_name)
    
    return render(request, 'site_admin/search_societies.html', {
        'form': form,
        'society_results': society_results,
    })

@login_required
@society_manager_or_admin_required
def edit_resources(request):
    # TODO: Check permissions on each resource
    assert request.method == 'POST'
    
    process_form = request.GET.get('process_form', None)
    return_url = request.GET.get('return_url')
    society_id = request.GET.get('society_id')
    assert(return_url is not None)
    
    resource_ids = request.POST.getlist('resource_ids')
    resources = [Resource.objects.get(id=resource_id) for resource_id in resource_ids]
    
    if process_form is not None:
        # Parse form
        form = EditResourcesForm(request.POST)
        if form.is_valid():
            
            # Assign tags to all resources
            assign_tags = form.cleaned_data['assign_tags']
            for resource in resources:
                for tag in assign_tags:
                    resource.nodes.add(tag)
                resource.save()
                for tag in assign_tags:
                    tag.save()
            
            # Assign priorities
            if form.cleaned_data['priority'] == 'yes':
                for resource in resources:
                    resource.priority_to_tag = True
                    resource.save()
                
            elif form.cleaned_data['priority'] == 'no':
                for resource in resources:
                    resource.priority_to_tag = False
                    resource.save()
            
            # Assign completed
            if form.cleaned_data['completed'] == 'yes':
                for resource in resources:
                    resource.completed = True
                    resource.save()
                
            elif form.cleaned_data['completed'] == 'no':
                for resource in resources:
                    resource.completed = False
                    resource.save()
            
            # Remove selected tags
            remove_tag_ids = request.POST.getlist('remove_tag_ids')
            remove_tags = [Node.objects.get(id=remove_tag_id) for remove_tag_id in remove_tag_ids]
            for resource in resources:
                for tag in remove_tags:
                    resource.nodes.remove(tag)
                resource.save()
                for tag in remove_tags:
                    tag.save()
            
            return HttpResponseRedirect(return_url)
            
    else:
        # Show the intial form
        form = EditResourcesForm(initial={
            'priority': 'no change',
            'completed': 'no change',
        })
    
    form.fields['assign_tags'].widget.set_society_id(society_id)
    
    # Find the common tags
    common_tags = None
    for resource in resources:
        if common_tags is None:
            common_tags = list(resource.nodes.all())
        else:
            i = 0
            while i < len(common_tags):
                tag = common_tags[i]
                if tag not in resource.nodes.all():
                    common_tags.remove(tag)
                else:
                    i += 1
    
    return render(request, 'site_admin/edit_resources.html', {
        'form': form,
        'resources': resources,
        'common_tags': common_tags,
        'return_url': return_url,
    })

@login_required
@admin_required
def list_resources(request, type1):
    if type1 == 'conferences':
        type1 = 'conference'
    elif type1 == 'standards':
        type1 = 'standard'
    elif type1 == 'periodicals':
        type1 = 'periodical'
    else:
        raise Exception('Unknown type "%s"' % type1)
        
    resource_type = ResourceType.objects.getFromName(type1)
    resources = Resource.objects.filter(resource_type=resource_type)
    return render(request, 'site_admin/list_resources.html', {
        'resource_type': resource_type,
        'resources': resources,
    })

@login_required
@society_manager_or_admin_required
def view_resource(request, resource_id):
    return_url = request.GET.get('return_url', '')
    resource = Resource.objects.get(id=resource_id)
    return render(request, 'site_admin/view_resource.html', {
        'return_url': return_url,
        'resource': resource,
    })

@login_required
@society_manager_or_admin_required
def edit_resource(request, resource_id=None):
    return_url = request.GET.get('return_url', '')
    society_id = request.GET.get('society_id', '')
    
    if resource_id is None:
        # creating a new resource
        if 'society_id' in request.GET:
            #raise Exception('query variable "society_id" not found')
            society = Society.objects.get(id=int(request.GET['society_id']))
            societies = [society]
        else:
            societies = []
        resource = None
        form = CreateResourceForm(initial={
            'societies': societies,
        })
        if not request.user.is_superuser:
            make_display_only(form.fields['conference_series'])
            make_display_only(form.fields['year'])
            make_display_only(form.fields['date'])
            make_display_only(form.fields['societies'], is_multi_search=True)
        show_standard_status = True
        
    else:
        # editing an existing resource
        resource = Resource.objects.get(id=resource_id)
        form = EditResourceForm(initial={
            'id': resource.id,
            'ieee_id': resource.ieee_id,
            'name': resource.name,
            'resource_type': resource.resource_type,
            'description': resource.description,
            'url': resource.url,
            'nodes': resource.nodes.all(),
            'societies': resource.societies.all(),
            'priority_to_tag': resource.priority_to_tag,
            'completed': resource.completed,
            'keywords': resource.keywords,
            'standard_status': resource.standard_status,
            'conference_series': resource.conference_series,
            'year': resource.year,
            'date': resource.date,
        })
        
        if society_id != '':
            form.fields['nodes'].widget.set_search_url(reverse('ajax_search_tags') + '?society_id=' + society_id)
            form.fields['nodes'].widget.set_society_id(society_id)
        
        # Disable edit resource form fields for societies
        if not request.user.is_superuser:
            make_display_only(form.fields['name'])
            make_display_only(form.fields['conference_series'])
            make_display_only(form.fields['societies'], is_multi_search=True)
            make_display_only(form.fields['ieee_id'])
            make_display_only(form.fields['keywords'])
            make_display_only(form.fields['standard_status'])
            make_display_only(form.fields['year'])
            make_display_only(form.fields['date'])
            show_standard_status = True
        else:
            if resource.resource_type.name == ResourceType.STANDARD:
                show_standard_status = True
            else:
                show_standard_status = False
    
    return render(request, 'site_admin/edit_resource.html', {
        'return_url': return_url,
        'society_id': society_id,
        'resource': resource,
        'form': form,
        'show_standard_status': show_standard_status,
    })

@login_required
@society_manager_or_admin_required
def save_resource(request):
    if 'return_url' not in request.GET:
        raise Exception('Query variable "return_url" not found')
    return_url = request.GET['return_url']
    
    if 'id' not in request.POST:
        form = CreateResourceForm(request.POST)
    else:
        form = EditResourceForm(request.POST)
    
    errors = []
    
    if form.is_valid():
        
        # Validate form
        if form.cleaned_data['resource_type'].name == ResourceType.STANDARD and form.cleaned_data['standard_status'] == '':
            errors.append('A Status is required for Standards')
        
        if len(errors) == 0:
            # Passed validation
            if 'id' in form.cleaned_data:
                # Existing resource
                resource = Resource.objects.get(id=form.cleaned_data['id'])
            else:
                # New resource
                resource = Resource.objects.create(
                    resource_type=form.cleaned_data['resource_type']
                )
            
            # Need to update these node totals later (in case the user has removed one from this resource)
            # NOTE: without list(), this becomes a lazy reference and is evaluated after the resource.svae() later on... need to call list() here to make a current copy.
            old_nodes = list(resource.nodes.all())
            
            resource.name = form.cleaned_data['name']
            resource.ieee_id = form.cleaned_data['ieee_id']
            resource.description = form.cleaned_data['description']
            resource.url = form.cleaned_data['url']
            resource.nodes = form.cleaned_data['nodes']
            if form.cleaned_data['societies'] is not None:
                resource.societies = form.cleaned_data['societies']
            resource.priority_to_tag = form.cleaned_data['priority_to_tag']
            resource.completed = form.cleaned_data['completed']
            resource.keywords = form.cleaned_data['keywords']
            if 'standard_status' in request.POST:
                resource.standard_status = form.cleaned_data['standard_status']
            resource.conference_series = form.cleaned_data['conference_series']
            resource.year = form.cleaned_data['year']
            resource.date = form.cleaned_data['date']
            resource.save()
            
            # Add all resource tags to the owning societies
            for society in resource.societies.all():
                for node in resource.nodes.all():
                    society.tags.add(node)
                society.save()
            
            # Update the node totals (for both the old & current nodes)
            _update_node_totals(old_nodes)
            _update_node_totals(resource.nodes.all())
            
            # Return to the society the user was editing
            if begins_with(return_url, 'close_window'):
                return HttpResponse("""
                    <script>
                        window.close();
                    </script>
                    <a href="javascript:window.close();">Close window</a>
                """)
            elif return_url == '':
                return HttpResponseRedirect(reverse('admin_view_resource', args=[resource.id]))
                
            else:
                return HttpResponseRedirect(return_url)
    
    # Re-render the form
    if 'id' in request.POST:
        resource = Resource.objects.get(id=int(request.POST['id']))
    else:
        resource = None
    
    # Disable edit resource form fields for societies
    if not request.user.is_superuser:
        make_display_only(form.fields['societies'], is_multi_search=True)
        make_display_only(form.fields['ieee_id'])
        
    return render(request, 'site_admin/edit_resource.html', {
        'return_url': return_url,
        'resource': resource,
        'form': form,
        'errors': list_to_html_list(errors),
    })
    

@login_required
@admin_required
def delete_resource(request, resource_id):
    next = request.GET.get('next')
    
    resource = Resource.objects.get(id=resource_id)
    old_nodes = resource.nodes.all()
    Resource.objects.get(id=resource_id).delete()
    _update_node_totals(old_nodes)
    return HttpResponseRedirect(next)

#@login_required
#@society_manager_or_admin_required
#@transaction.commit_on_success
#def remove_priorities(request):
#    """
#    Removes priorities from resources according to the requirements.  Only the following should have priority = True:
#    - 2009 Conferences
#    - Published Standards
#    - All publications
#    """
#    permissions.require_superuser(request)
#    logging.debug('remove_priorities()')
#    
#    # Remove priority from all non-2009 conferences
#    conferences = Resource.objects.get_conferences()
#    logging.debug('  conferences.count(): %s' % conferences.count())
#    conferences = conferences.exclude(year='2009')
#    logging.debug('  non-2009 conferences.count(): %s' % conferences.count())
#    conferences.update(priority_to_tag=False)
#    
#    standards = Resource.objects.get_standards()
#    logging.debug('  standards.count(): %s' % standards.count())
#    standards = standards.exclude(standard_status=Resource.STANDARD_STATUS_PUBLISHED)
#    logging.debug('  non-published standards.count(): %s' % standards.count())
#    standards.update(priority_to_tag=False)
#    
#    return HttpResponseRedirect(reverse('admin_priority_report'))
    

@login_required
@admin_required
def search_resources(request):
    resource_results = None
    if request.method == 'GET':
        form = SearchResourcesForm()
    else:
        form = SearchResourcesForm(request.POST)
        if form.is_valid():
            resource_name = form.cleaned_data['resource_name']
            resource_results = Resource.objects.searchByNameSubstring(resource_name)
    
    return render(request, 'site_admin/search_resources.html', {
        'form': form,
        'resource_results': resource_results,
    })

@login_required
@society_manager_or_admin_required
def ajax_search_tags(request):
    #MAX_RESULTS = 50
    
    society_id = request.GET.get('society_id', '')
    if society_id != '':
        society = Society.objects.get(id=society_id)
    else:
        society = None
    
    filter_sector_ids = request.GET.get('filter_sector_ids', None)
    if filter_sector_ids is not None:
        #sectors = [Node.objects.get(id=sector_id) for sector_id in filter_sector_ids.split(',')]
        sector_ids = [sector_id for sector_id in filter_sector_ids.split(',')]
    else:
        sector_ids = None
    
    exclude_tag_id = request.GET.get('exclude_tag_id', None)
    
    search_for = request.GET['search_for']
    if society_id != '':
        temp_society_id = int(society_id)
    else:
        temp_society_id = None
    tags = Node.objects.searchTagsByNameSubstring(search_for, sector_ids, exclude_tag_id, temp_society_id)
    
    tags = Node.objects.get_extra_info(tags)
    
    #if len(tags) > MAX_RESULTS:
    #    tags = tags[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if tags:
        for tag in tags:
            societies = []
            for society1 in tag.societies.all():
                societies.append({
                    'id': society1.id,
                    'name': society1.name,
                })
                
            data['options'].append({
                'name': tag.name,
                'name_link': reverse('admin_edit_tag', args=[tag.id]) + '?return_url=%s' % quote('/admin/?hash=' + quote('#tab-tags-tab')),
                'value': tag.id,
                'tag_name': tag.name,
                'sector_names': tag.sector_names(),
                'num_societies': tag.num_societies1,
                'num_related_tags': tag.num_related_tags1,
                'num_filters': tag.num_filters1,
                'num_resources': tag.num_resources1,
                'societies': societies,
            })
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="application/json")

@login_required
@society_manager_or_admin_required
def ajax_search_resources(request):
    #MAX_RESULTS = 50
    
    search_for = request.GET['search_for']
    #resources = Resource.objects.searchByNameSubstring(search_for)[:MAX_RESULTS+1]
    resources = Resource.objects.searchByNameSubstring(search_for)
    
    #if len(resources) > MAX_RESULTS:
    #    resources = resources[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if resources:
        for resource in resources:
            data['options'].append({
                'name': resource.name,
                'value': resource.id,
            })
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="application/json")

@login_required
@society_manager_or_admin_required
def ajax_search_societies(request):
    #MAX_RESULTS = 50
    
    search_for = request.GET['search_for']
    #societies = Society.objects.searchByNameSubstring(search_for)[:MAX_RESULTS+1]
    societies = Society.objects.searchByNameSubstring(search_for)
    
    #if len(societies) > MAX_RESULTS:
    #    societies = societies[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if societies:
        for society in societies:
            data['options'].append({
                'name': society.name,
                'value': society.id,
            })
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="application/json")
    
@login_required
@society_manager_or_admin_required
def ajax_update_society(request):
    action = request.POST.get('action')
    society_id = request.POST.get('society_id')
    tag_id = request.POST.get('tag_id')
    
    if action == 'add_tag':
        society = Society.objects.get(id=society_id)
        tag = Node.objects.get(id=tag_id)
        society.tags.add(tag)
        return HttpResponse('success')
    
    elif action == 'remove_tag':
        society = Society.objects.get(id=society_id)
        tag = Node.objects.get(id=tag_id)
        society.tags.remove(tag)
        return HttpResponse('success')
    
    else:
        raise Exception('Unknown action "%s"' % action)

def _response_csv_attachment(rows, filename):
    "Returns an HttpResponse() setup with the data in CSV format, saved as an attachment."
    buffer = StringIO.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    response = HttpResponse(buffer.getvalue(), 'text/csv')
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

@login_required
@admin_required
def login_report(request):
    export_csv = bool(request.GET.get('export_csv', False))
    users = UserManager.get_users_by_login_date() 
    if export_csv:
        # Export as a CSV file
        data = []
        data.append(['Username', 'Last Login Time'])
        for user in users:
            data.append([
                user.username,
                user.get_profile().last_login_time,
            ])
        filename = 'login_report_%s.csv' % datetime.today().strftime('%Y-%m-%d')
        return _response_csv_attachment(data, filename)
        
    else:
        # Render to browser
        return render(request, 'site_admin/login_report.html', {
            'users': users,
        })

@login_required
@admin_required
def tagged_resources_report(request, filter):
    export_csv = bool(request.GET.get('export_csv', False))
    
    if filter == 'priority':
        resources = Resource.objects.filter(priority_to_tag=True)
    elif filter == 'all':
        resources = Resource.objects.all()
    else:
        raise Exception('Unknown filter "%s"' % filter)
    
    # Calc the overall totals
    
    all_tagged_resources = 0
    all_total_resources = resources.count()
    
    for resource in resources:
        if resource.nodes.count() > 0:
            all_tagged_resources += 1
    
    all_percent_resources = all_tagged_resources / float(all_total_resources) * 100
    
    # Calc per-society totals
    
    societies = Society.objects.all()
    
    result_societies = []
    
    for society in societies:
        if filter == 'priority':
            society_resources = society.resources.filter(priority_to_tag=True)
        elif filter == 'all':
            society_resources = society.resources.all()
        total_resources = society_resources.count()
        num_tagged_resources = 0
        for resource in society_resources:
            if resource.nodes.count() > 0:
                num_tagged_resources += 1
        if total_resources == 0:
            percent_resources = 0
        else:
            percent_resources = num_tagged_resources / float(total_resources) * 100
        result_societies.append({
            'name': society.name,
            'total_resources': total_resources,
            'num_tagged_resources': num_tagged_resources,
            'percent_resources': percent_resources,
        })
    
    if export_csv:
        # Export as a CSV file
        data = []
        data.append(['Name', 'Tagged', 'Total', 'Percent'])
        data.append([
            'All Resources',
            all_tagged_resources,
            all_total_resources,
            '%s%%' % all_percent_resources
        ])
        
        for society in result_societies:
            data.append([
                society['name'],
                society['num_tagged_resources'],
                society['total_resources'],
                '%s%%' % society['percent_resources']
            ])
        filename = 'login_report_%s.csv' % datetime.today().strftime('%Y-%m-%d')
        return _response_csv_attachment(data, filename)
        
    else:
        # Render to browser
        return render(request, 'site_admin/tagged_resources_report.html', {
            'filter': filter,
            'all_tagged_resources': all_tagged_resources,
            'all_total_resources': all_total_resources,
            'all_percent_resources': all_percent_resources,
            'societies': result_societies,
        })

@login_required
@admin_required
def tags_report(request):
    export_csv = bool(request.GET.get('export_csv', False))
    
    start = time.time()
    
    # Calc the overall totals
    
    tags = Node.objects.get_tags().extra(
        select={
            'num_filters': 'SELECT COUNT(*) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id',
            'num_resources1': 'SELECT COUNT(*) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id',
            'num_societies': 'SELECT COUNT(*) FROM ieeetags_node_societies WHERE ieeetags_node_societies.node_id = ieeetags_node.id',
        }
    )
    
    all_total_tags = tags.count()
    all_filtered_tags = 0
    all_society_tags = 0
    all_resource_tags = 0
    for tag in tags:
        if tag.num_filters > 0:
            all_filtered_tags += 1
        if tag.num_societies > 0:
            all_society_tags += 1
        if tag.num_resources1 > 0:
            all_resource_tags += 1
    
    all_percent_filtered = all_filtered_tags / float(all_total_tags) * 100
    all_percent_society = all_society_tags / float(all_total_tags) * 100
    all_percent_resource = all_resource_tags / float(all_total_tags) * 100
    
    # Calc per-society totals
    
    societies = Society.objects.all()
    
    result_societies = []
    
    for society in societies:
        
        society_tags = society.tags.extra(
            select={
                'num_filters': 'SELECT COUNT(*) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id',
                'num_resources1': 'SELECT COUNT(*) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id',
                'num_societies': 'SELECT COUNT(*) FROM ieeetags_node_societies WHERE ieeetags_node_societies.node_id = ieeetags_node.id',
            }
        )
        
        total_tags = society.tags.count()
        
        filtered_tags = 0
        for tag in society_tags:
            if tag.num_filters > 0:
                filtered_tags += 1
        if total_tags == 0:
            percent_filtered = 0
        else:
            percent_filtered = filtered_tags / float(total_tags) * 100
        
        resource_tags = 0
        for tag in society_tags:
            if tag.num_resources1 > 0:
                resource_tags += 1
        if total_tags == 0:
            percent_resource = 0
        else:
            percent_resource = resource_tags / float(total_tags) * 100
        
        result_societies.append({
            'name': society.name,
            'total_tags': total_tags,
            'filtered_tags': filtered_tags,
            'percent_filtered': percent_filtered,
            'resource_tags': resource_tags,
            'percent_resource': percent_resource,
        })
    
    #print 'all_filtered_tags:', all_filtered_tags
    #print 'all_total_tags:', all_total_tags
    #print 'all_percent_filtered:', all_percent_filtered
    
    end = time.time()

    if export_csv:
        # Export as a CSV file
        data = []
        data.append(['Name', 'Total', '# Filtered', '% Filtered', '# Resources', '% Resources', '# Societies', '% Societies'])
        data.append([
            'All Tags',
            all_total_tags,
            all_filtered_tags,
            '%s%%' % all_percent_filtered,
            all_resource_tags,
            '%s%%' % all_percent_resource,
            all_society_tags,
            '%s%%' % all_percent_society,
        ])
        
        for society in result_societies:
            data.append([
                society['name'],
                society['total_tags'],
                society['filtered_tags'],
                '%s%%' % society['percent_filtered'],
                society['resource_tags'],
                '%s%%' % society['percent_resource'],
            ])
        filename = 'tags_report_%s.csv' % datetime.today().strftime('%Y-%m-%d')
        return _response_csv_attachment(data, filename)
        
    else:
        # Render to browser
        return render(request, 'site_admin/tags_report.html', {
            'all_total_tags': all_total_tags,
            'all_filtered_tags': all_filtered_tags,
            'all_percent_filtered': all_percent_filtered,
            'all_society_tags': all_society_tags,
            'all_percent_society': all_percent_society,
            'all_resource_tags': all_resource_tags,
            'all_percent_resource': all_percent_resource,
            'societies': result_societies,
            'page_time': end-start,
        })

@login_required
@admin_required
def clusters_report(request):
    clusters = Node.objects.get_clusters()
    return render(request, 'site_admin/clusters_report.html', {
        'clusters': clusters,
    })

@login_required
@admin_required
def priority_report(request):
    "Show the priorities for resources."
    export_csv = bool(request.GET.get('export_csv', False))
    
    results = odict()
    
    conferences = Resource.objects.get_conferences()
    results['All Conferences'] = conferences.count(), conferences.filter(priority_to_tag=True).count()
    
    conferences_2009 = conferences.filter(year='2009')
    results['2009 Conferences'] = conferences_2009.count(), conferences_2009.filter(priority_to_tag=True).count()
    
    conferences_non_2009 = conferences.exclude(year='2009')
    results['Non-2009 Conferences'] = conferences_non_2009.count(), conferences_non_2009.filter(priority_to_tag=True).count()
    
    standards = Resource.objects.get_standards()
    results['All Standards'] = standards.count(), standards.filter(priority_to_tag=True).count()
    
    published_standards = standards.filter(standard_status=Resource.STANDARD_STATUS_PUBLISHED)
    results['Published Standards'] = published_standards.count(), published_standards.filter(priority_to_tag=True).count()
    
    unpublished_standards = standards.exclude(standard_status=Resource.STANDARD_STATUS_PUBLISHED)
    results['Unpublished Standards'] = unpublished_standards.count(), unpublished_standards.filter(priority_to_tag=True).count()
    
    periodicals = Resource.objects.get_periodicals()
    results['All Periodicals'] = periodicals.count(), periodicals.filter(priority_to_tag=True).count()
    
    if export_csv:
        # Export as a CSV file
        data = []
        for name, values in results.items():
            data.append([
                name,
                values[0],
                values[1],
            ])
        filename = 'priority_report_%s.csv' % datetime.today().strftime('%Y-%m-%d')
        return _response_csv_attachment(data, filename)
        
    else:
        # Render to browser
        return render(request, 'site_admin/priority_report.html', {
            'results': results,
        })

def _get_duplicate_tags():
    "Performs a raw SQL query to get any duplicate tags."
    from django.db import connection, transaction
    cursor = connection.cursor()
    cursor.execute("""
        SELECT tag1.name, tag1.id AS id1, tag2.id AS id2
        FROM `ieeetags_node` tag1, ieeetags_node tag2
        WHERE tag1.name = tag2.name AND tag1.id < tag2.id
        AND tag1.node_type_id = 3 AND tag2.node_type_id = 3
    """)
    #    LIMIT 5
    rows = cursor.fetchall()
    return rows

@login_required
@admin_required
def duplicate_tags_report(request):
    "Show any duplicate tags."
    export_csv = bool(request.GET.get('export_csv', False))
    start = time.time()
    
    duplicate_tags = _get_duplicate_tags()
    duplicate_tags_json = json.dumps(duplicate_tags)
    
    page_time = time.time() - start
    logging.debug('page_time: %s'  % page_time)
    
    if export_csv:
        # Export as a CSV file
        data = []
        data.append(['Tag name', 'ID1', 'ID2'])

        for tag in duplicate_tags:
            data.append([
                tag[0],
                tag[1],
                tag[2],
            ])
        filename = 'duplicate_tags_report_%s.csv' % datetime.today().strftime('%Y-%m-%d')
        return _response_csv_attachment(data, filename)
        
    else:
        # Render to browser
        return render(request, 'site_admin/duplicate_tags_report.html', {
            'duplicate_tags': duplicate_tags,
            'duplicate_tags_json': duplicate_tags_json,
            'page_time': page_time,
        })

def remove_prefix(prefix, filename):
    prefix = os.path.normpath(prefix)
    filename = os.path.normpath(filename)
    if not filename.startswith(prefix):
        raise Exception('filename "%s" doesn\'t start with prefix "%s"' % (filename, prefix))
    filename = filename[len(prefix):]
    if len(filename) > 0 and filename[0] == '\\':
        filename = filename[1:]
    return filename

@login_required
@admin_required
def society_logos_report(request):
    societies = Society.objects.all()
    
    logos_path = os.path.join(settings.MEDIA_ROOT, 'images', 'sc_logos')
    full_logos_path = os.path.join(settings.MEDIA_ROOT, 'images', 'sc_logos', 'full')
    thumbnail_logos_path = os.path.join(settings.MEDIA_ROOT, 'images', 'sc_logos', 'thumbnail')
    
    new_logos_count = 0
    for society in societies:
        logo_filename = os.path.join(logos_path, society.abbreviation.lower() + '.jpg')
        if os.path.exists(logo_filename):
            print 'found logo'
            
            from PIL import Image
            import shutil
            
            MAX_WIDTH = 100
            MAX_HEIGHT = 100
            
            image = Image.open(logo_filename)
                
            # Create a thumbnail of the original logo
            full_logo_filename = os.path.join(full_logos_path, society.abbreviation.lower() + '.jpg')
            thumbnail_logo_filename = os.path.join(thumbnail_logos_path, society.abbreviation.lower() + '.jpg')
            image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.ANTIALIAS)
            image.save(thumbnail_logo_filename)
            del image
            
            # Move the original to the "full" folder
            shutil.move(logo_filename, full_logo_filename)
            
            society.logo_full = remove_prefix(settings.MEDIA_ROOT, full_logo_filename)
            society.logo_thumbnail = remove_prefix(settings.MEDIA_ROOT, thumbnail_logo_filename)
            society.save()
            
            new_logos_count += 1
    
    return render(request, 'site_admin/society_logos_report.html', {
        'societies': societies,
        'new_logos_count': new_logos_count,
    })

@login_required
@admin_required
def conference_series_report(request):
    conferences = []
    serieses = Resource.objects.get_conference_series()

    # Get the newest conference for each series
    for conference_series, num_in_series in serieses:
        # Get most recent conference for the series
        resource = Resource.objects.get_current_conference_for_series(conference_series)
        # TODO: Get only other conferences from this society
        resource.other_conferences = Resource.objects.get_non_current_conferences_for_series(conference_series, current_conference=resource)
        conferences.append(resource)
    
    return render(request, 'site_admin/conference_series_report.html', {
        'serieses': serieses,
        'conferences': conferences,
    })

def _get_active_url_checker():
    # Get the most recently-started active log
    url_checker_log = UrlCheckerLog.objects.filter(date_ended=None).order_by('-date_started')
    if url_checker_log.count() > 0:
        url_checker_log = url_checker_log[0]
        delta = (datetime.now() - url_checker_log.date_started)
        delta = delta.days * 60*60*24 + delta.seconds
        # 5 minute timeout
        if delta > 5*60:
            # The last checker has been idle > 5 minutes, assume it's dead and close it out.
            url_checker_log.date_ended = datetime.now()
            url_checker_log.save()
            return None
        else:
            return url_checker_log
    else:
        return None

@login_required
@admin_required
def broken_links_report(request):
    bad_resources = Resource.objects.filter(url_status=Resource.URL_STATUS_BAD)
    
    num_resources = Resource.objects.all().count()
    num_url_resources = Resource.objects.exclude(url='').count()
    num_good_resources = Resource.objects.filter(url_status=Resource.URL_STATUS_GOOD).count()
    num_unchecked_resources = Resource.objects.exclude(url='').filter(url_status='').count()
    num_checked_resources = num_good_resources + bad_resources.count()
    
    url_checker_log = _get_active_url_checker()

    return render(request, 'site_admin/broken_links_report.html', {
        'bad_resources': bad_resources,
        'num_resources': num_resources,
        'num_url_resources': num_url_resources,
        'num_good_resources': num_good_resources,
        'num_unchecked_resources': num_unchecked_resources,
        'num_checked_resources': num_checked_resources,
        'url_checker_log': url_checker_log,
    })

@login_required
@admin_required
def broken_links_reset(request, reset_type, resource_id=None):
    if reset_type == 'all':
        # Reset all resources
        Resource.objects.update(url_status='')
    elif reset_type == 'timed_out':
        # Reset 'Timed Out' resources
        Resource.objects.filter(url_status=Resource.URL_STATUS_BAD, url_error='Timed out').update(url_status='')
    elif reset_type == 'resource':
        # Reset a specific resource
        Resource.objects.filter(id=resource_id).update(url_status='')
    else:
        raise Exception('Unknown reset_type "%s"' % reset_type)
    return HttpResponseRedirect(reverse('admin_broken_links_report'))

@login_required
@admin_required
def broken_links_check(request, check_type=None, resource_id=None):
    print 'broken_links_check()'
    
    next = request.GET.get('next', '')
    
    if check_type is None:
        # Get all resources with URLs that have not yet been checked
        resources = Resource.objects.exclude(url='').filter(url_status='')
        
        # Start the URL checking thread (daemon, so it continues to run after this function returns to the browser)
        thread = threading.Thread(target=url_checker.check_resources, args=[resources], kwargs={ 'num_threads': 10 })
        thread.setDaemon(True)
        thread.start()
    elif check_type == 'resource':
        # Just check a single resource
        if resource_id is None:
            raise Exception('Must specify resource_id when check_type is "resource".')
        resources = Resource.objects.filter(id=resource_id)
        
        # Check the resource synchronously (don't use threads)
        url_checker.check_resources(resources, num_threads=1)
    
    if next != '':
        return HttpResponseRedirect(next)
    else:
        return HttpResponseRedirect(reverse('admin_broken_links_report'))

@login_required
@admin_required
def broken_links_cancel(request):
    url_checker_log = _get_active_url_checker()
    if url_checker_log is not None:
        url_checker_log.date_ended = datetime.now()
        url_checker_log.status = 'Cancelled.'
        url_checker_log.save()
    return HttpResponseRedirect(reverse('admin_broken_links_report'))

#def create_admin_login(request):
#    "Create a test admin account."
#    username = 'test'
#    password = 'test'
#    email = 'test'
#    User.objects.filter(username=username).delete()
#    user = User.objects.create_user(
#        username=username,
#        password=password,
#        email=email,
#    )
#    user.is_active = True
#    user.is_staff = True
#    user.is_superuser = True
#    user.save()
#    
#    profile = user.get_profile()
#    profile.role = Profile.ROLE_ADMIN
#    profile.save()
#    
#    print 'user:', user
#    print 'user.username:', user.username
#    print 'user.password:', user.password
#    
#    assert False, 'User has been created'
    
@society_manager_or_admin_required
def export_tab_resources(request):
    "Export all resources for the TAB society in CSV format."
    #print 'export_tab_resources()'
    filename = os.path.realpath('../tab_resources.csv')
    #print 'filename:', filename
    file = codecs.open(filename, 'w', encoding='utf-8')
    
    tab_society = Society.objects.getFromAbbreviation('TAB')
    assert tab_society is not None
    
    # Write the header row
    row = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s"\r\n' % (
        'Type',
        'ID',
        'Name',
        'Description',
        'URL',
        'Tags',
        'Society Abbreviations',
        'Conference Year',
        'Standard Status',
        'Standard Technical Committees',
        'Keywords',
        'Priority',
    )
    file.write(row)
    
    for resource in tab_society.resources.all():
        row = '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\r\n' % (
            _escape_csv_field(resource.resource_type.name),
            _escape_csv_field(resource.id),
            _escape_csv_field(resource.name),
            _escape_csv_field(resource.description),
            _escape_csv_field(resource.url),
            _escape_csv_field(','.join([node.name for node in resource.nodes.all()])),
            _escape_csv_field(','.join([society.abbreviation for society in resource.societies.all()])),
            _escape_csv_field(resource.year),
            _escape_csv_field(resource.standard_status),
            _escape_csv_field(''),
            _escape_csv_field(resource.keywords),
            _escape_csv_field(bool(resource.priority_to_tag)),
        )
        file.write(row)
    
    file.close()
    
    file = codecs.open(filename, 'r', encoding='utf-8')
    contents = file.read()
    file.close()
    
    return HttpResponse(contents, 'text/plain')

@login_required
def admin_info(request):
    
    contents = []
    contents.append('<h1>Info</h1>')
    contents.append('')
    contents.append('sys.path:')
    for path in sys.path:
        contents.append('    %s' % path)
    
    import models
    contents.append('models.Node: %r' % models.Node)
    
    return HttpResponse('\r\n'.join(contents), 'text/plain')
