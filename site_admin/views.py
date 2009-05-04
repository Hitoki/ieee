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
import time
from urllib import quote
import warnings
from django.db import IntegrityError
from django.db import transaction
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import simplejson as json

from ieeetags import settings
from ieeetags import permissions
from ieeetags.util import *
from ieeetags.models import Node, NodeType, Permission, Resource, ResourceType, Society, Filter, Profile, get_user_from_username, get_user_from_email, UserManager
#, UserManager2
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
    path = relpath(__file__, '../version.txt')
    #print 'path:', path
    file = open(path, 'r')
    version = file.readline().strip()
    date = file.readline().strip()
    file.close()
    #print 'version:', version
    if version == '$WCREV$':
        version = 'SVN'
        
        from subprocess import Popen, PIPE
        try:
            proc = Popen('svn info "%s"' % path, stdout=PIPE)
            proc.wait()
            for line in proc.stdout:
                matches = re.match(r'Last Changed Rev: (\d+)', line)
                if matches:
                    version = matches.group(1) + '-svn'
                matches = re.match(r'Last Changed Date: (\S+ \S+)', line)
                if matches:
                    date = matches.group(1)
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        except Exception:
            version = 'UNKNOWN'
            date = ''
            
        #print 'version:', version
        #print 'date:', date
    
    return version, date

def _update_node_totals(nodes):
    for node in nodes:
        node.num_resources = node.resources.count()
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
""" % (abs_reset_url)
    
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
    value = value.replace(u'"', u'""')
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
    
# ------------------------------------------------------------------------------

def login(request):
    next = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
    else:
        form = LoginForm()
    if not form.is_valid():
        return render(request, 'site_admin/login.html', {
            'next': next,
            'show_society_login_banner': settings.SHOW_SOCIETY_LOGIN_BANNER,
            'form': form,
        })
    else:
        user = auth.authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is None:
            return render(request, 'site_admin/login.html', {
                'error': 'Invalid login, please try again.',
                'next': next,
                'show_society_login_banner': settings.SHOW_SOCIETY_LOGIN_BANNER,
                'form': form,
            })
        elif user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER and user.societies.count() == 0:
            return render(request, 'site_admin/login.html', {
                'error': 'Your account has not been assigned to a society yet.  Please contact the administrator to fix this.',
                'next': next,
                'show_society_login_banner': settings.SHOW_SOCIETY_LOGIN_BANNER,
                'form': form,
            })
        else:
            # Successful login
            auth.login(request, user)
            
            profile = user.get_profile()
            profile.last_login_time = datetime.now()
            profile.save()
            
            if next != '':
                return HttpResponseRedirect(next)
            else:
                return HttpResponseRedirect(reverse('admin_home'))

def logout(request):
    if request.user.is_authenticated:
        profile = request.user.get_profile()
        profile.last_logout_time = datetime.now()
        profile.save()
    auth.logout(request)
    return HttpResponsePermanentRedirect(reverse('admin_home'))

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
                # Successfully changed password
                request.user.set_password(form.cleaned_data['password1'])
                request.user.save()
                
                # Send the password change email
                _send_password_change_notification(request.user)
                
                return HttpResponseRedirect(reverse('change_password_success'))
                
    return render(request, 'site_admin/change_password.html', {
        'error': error,
        'form': form,
    })

@login_required
def change_password_success(request):
    return render(request, 'site_admin/change_password_success.html')

@login_required
def home(request):
    role = request.user.get_profile().role
    
    if role == Profile.ROLE_ADMIN:
        # Show the admin home page
        version, date = _get_version()
        
        num_societies = Society.objects.count()
        num_society_managers = UserManager.get_society_managers().count()
        num_sectors = Node.objects.getSectors().count()
        num_tags = Node.objects.getTags().count()
        num_resources = Resource.objects.count()
        
        return render(request, 'site_admin/admin_home.html', {
            'version': version,
            'date': date,
            'num_societies': num_societies,
            'num_society_managers': num_society_managers,
            'num_sectors': num_sectors,
            'num_tags': num_tags,
            'num_resources': num_resources,
        })
        
    elif role == Profile.ROLE_SOCIETY_MANAGER:
        # Redirect to the society manager home page
        hash = request.GET.get('hash', '')
        
        # Only one society, just redirect to that view page
        if request.user.societies.count() == 1:
            return HttpResponseRedirect(reverse('admin_manage_society', args=[request.user.societies.all()[0].id]) + hash)
        
        # Has more than one society, show list of societies
        elif request.user.societies.count() > 1:
            #return HttpResponseRedirect(reverse('admin_societies'))
            return HttpResponseRedirect(reverse('admin_home_societies_list') + hash)
        
        else:
            raise Exception('User is a society manager but is not assigned to any societies.')
        
    else:
        raise Exception('Unknown role %s' % role)

@login_required
def home_societies_list(request):
    permissions.require_superuser(request)
    
    societies = Society.objects.getForUser(request.user)
    return render(request, 'site_admin/home_societies_list.html', {
        'societies': societies,
    })

@login_required
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
            
            # Make sure that user belongs to the specified society
            assert(request.user.societies.filter(id=society.id).count() > 0)
            
            # Send email
            subject = 'Missing resource for "%s" society.' % request.user.username
            message = 'Sent on %s:\n' % time.strftime('%Y-%m-%d %H:%M:%S') \
                + 'From: %s (%s)\n' % (request.user.username, request.user.email) \
                + 'Type of resource: %s\n\n' % form.cleaned_data['resource_type'] \
                + 'Description:\n' \
                + '%s\n\n' % form.cleaned_data['description']
            send_from = settings.DEFAULT_FROM_EMAIL
            send_to = settings.ADMIN_EMAILS
            
            logging.debug('send_to: %s' % send_to)
            logging.debug('send_from: %s' % send_from)
            logging.debug('subject: %s' % subject)
            logging.debug('message: %s' % message)
            
            try:
                send_mail(subject, message, send_from, send_to)
            except Exception, e:
                logging.error('Error sending missing resource email: %s' % e)
                email_error = True
            else:
                email_error = False
            
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
def update_tag_counts(request):
    permissions.require_superuser(request)
    
    start = time.time()
    numTags = Node.objects.updateTagCounts()
    return render(request, 'site_admin/update_tag_counts.html', {
        'pageTime': time.time()-start,
        'numTags': numTags,
    })

@login_required
@transaction.commit_on_success
def import_tags(request, source):
    permissions.require_superuser(request)
    
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
            
            sectors = [Node.objects.getSectorByName(sector_name) for sector_name in sector_names]
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
@transaction.commit_on_success
def unassigned_tags(request):
    permissions.require_superuser(request)
    
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

@login_required
def import_societies(request, source):
    permissions.require_superuser(request)
    
    logging.debug('import_societies()')
    start = time.time()
    
    if source == 'v.7':
        filename = relpath(__file__, '../data/v.7/2009-04-20 - societies - fixed.csv')
    elif source == 'comsoc':
        filename = relpath(__file__, '../data/comsoc/societies.csv')
    else:
        raise Exception('Unknown source "%s"' % source)
        
    logging.debug('  filename: %s' % filename)
    
    # Delete all existing societies
    Society.objects.all().delete()
    
    # Get a unicode CSV reader
    (file, reader) = _open_unicode_csv_reader(filename)
    
    row_count = 0
    societies_created = 0
    tags_created = 0
    bad_tags = []
    
    for row in reader:
        #print 'row:', row
        
        # Name, Abbreviation, URL, Tags
        society_name, abbreviation, url, tag_names = row
        tag_names = [tag.strip() for tag in _split_no_empty(tag_names, ',')]
        
        # Formatting
        society_name = _remove_society_acronym(society_name.strip())
        
        tags = []
        for tag_name in tag_names:
            #print '  tag_name:', tag_name
            tag = Node.objects.get_tag_by_name(tag_name)
            if tag is None:
                #raise Exception('Can\'t find matching tag "%s"' % tag_name)
                logging.error('    Can\'t find matching tag "%s"' % tag_name)
                if tag_name not in bad_tags:
                    bad_tags.append(tag_name)
            else:
                tags.append(tag)
        
        society = Society.objects.create(
            name=society_name,
            abbreviation=abbreviation,
            url=url,
        )
        society.tags = tags
        society.save()
        
        societies_created += 1
        
        row_count += 1
        if not row_count % 10:
            logging.debug('  Parsing row %d' % row_count)
        
    file.close()
    
    bad_tags = '<br/>\n'.join(sorted(bad_tags))
    
    return render(request, 'site_admin/import_results.html', {
        'page_title': 'Import Societies',
        'results': {
            'page_time': time.time()-start,
            'row_count': row_count,
            'societies_created': societies_created,
            'bad_tags': bad_tags,
        }
    })

@login_required
def fix_societies_import(request):
    permissions.require_superuser(request)
    
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
    
def _import_resources(filename, batch_commits=False):
    #logging.debug('_import_resources()')
    
    start = time.time()
    
    row_count = 0
    duplicate_resources = 0
    resources_added = 0
    societies_assigned = 0
    num_invalid_societies = 0
    resources_skipped = 0
    
    (file, reader) = _open_unicode_csv_reader(filename)
    
    #print 'filename:', filename
    
    valid_societies = {}
    invalid_societies = {}
    
    for row in reader:
        
        #Type, ID, Name, Description, URL, Tags, Society Abbreviations, Year, Standard Status, Technical Committees, Keywords, Priority
        type1, ieee_id, name, description, url, tag_names, society_abbreviations, year, standard_status, technical_committees, keywords, priority_to_tag = row
        
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
                        )
                        resource.societies = societies
                        resource.save()
                        resources_added += 1
                    
        if not row_count % 50:
            try:
                logging.debug('    Parsing row %d, row/sec %f' % (row_count, row_count/(time.time()-start) ))
            except Exception:
                pass
            
        row_count += 1
        
        if batch_commits and not row_count % 300:
            #logging.debug('    committing transaction.')
            transaction.commit()
        
        # DEBUG:
        #if row_count > 50:
        #    transaction.commit()
        #    break

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
        'resources_added': resources_added,
        'societies_assigned': societies_assigned,
        'num_invalid_societies': num_invalid_societies,
        'valid_societies': valid_societies,
        'invalid_societies': invalid_societies,
        'resources_skipped': resources_skipped,
    }

@login_required
@transaction.commit_manually
def import_conferences(request, source):
    permissions.require_superuser(request)
    
    start = time.time()
    
    if source not in _IMPORT_SOURCES:
        raise Exception('Unknown import source "%s"' % source)
    
    if source == 'comsoc':
        filename = relpath(__file__, '../data/comsoc/conferences.csv')
    elif source == 'v.7':
        filename = relpath(__file__, '../data/v.7/2009-04-21 - conferences.csv')

    # Delete all conferences
    Resource.objects.get_conferences().delete()
    transaction.commit()
    
    # Import conferences
    results = _import_resources(filename, batch_commits=True)
    
    results['page_time'] = time.time()-start
    
    return render(request, 'site_admin/import_results.html', {
        'page_title': 'Import Conferences',
        'results': results,
    })

@login_required
@transaction.commit_on_success
def import_periodicals(request, source):
    permissions.require_superuser(request)
    
    start = time.time()
    
    if source not in _IMPORT_SOURCES:
        raise Exception('Unknown import source "%s"' % source)
    
    if source == 'comsoc':
        raise Exception('There is no periodicals file for COMSOC')
    elif source == 'v.7':
        filename = relpath(__file__, '../data/v.7/2009-04-23c - publications.csv')

    # Delete all periodicals
    Resource.objects.get_periodicals().delete()
    
    # Import periodicals
    results = _import_resources(filename)
    
    return render(request, 'site_admin/import_resources.html', {
        'page_title': 'Import Periodicals',
        'page_time': time.time()-start,
        'results': results,
    })

@login_required
@transaction.commit_on_success
def import_standards(request, source):
    permissions.require_superuser(request)
    
    start = time.time()
    
    #filename = relpath(__file__, '../data/comsoc/standards.csv')
    if source == 'v.7':
        filename = relpath(__file__, '../data/v.7/2009-04-23b - standards.csv')
    else:
        raise Exception('Unknown source "%s".' % source)
    
    # Delete all standards
    Resource.objects.get_standards().delete()
    
    # Import standards
    results = _import_resources(filename)
    
    return render(request, 'site_admin/import_resources.html', {
        'page_title': 'Import Standards',
        'page_time': time.time()-start,
        'results': results,
    })

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
def fix_user_import(request):
    permissions.require_superuser(request)
    
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
@transaction.commit_manually
def import_users(request):
    permissions.require_superuser(request)
    
    if request.method == 'GET':
        # Display form
        form = ImportUsersForm()
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
                raise Exception('Unknown role "%s"' % role)
            
            if username == '':
                raise Exception('Username is blank')
            
            if email == '':
                raise Exception('Email is blank')
            
            society_abbreviations = [society_abbreviation.strip() for society_abbreviation in _split_no_empty(society_abbreviations, ',')]
            
            societies = []
            for society_abbreviation in society_abbreviations:
                society = Society.objects.getFromAbbreviation(society_abbreviation)
                if society is None:
                    raise Exception('Unknown society "%s"' % society_abbreviation)
                societies.append(society)
            
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
        
        logging.debug('~import_users()')
        
        if len(errors) > 0:
            # Errors, rollback all changes & reset stats
            transaction.rollback()
        else:
            # Success, commit transaction
            transaction.commit()
        
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
def list_sectors(request):
    permissions.require_superuser(request)
    
    sectors = Node.objects.getSectors()
    return render(request, 'site_admin/list_sectors.html', {
        'sectors': sectors,
    })

@login_required
def view_sector(request, sectorId):
    permissions.require_superuser(request)
    
    sector = Node.objects.get(id=sectorId)
    
    #for i in dir(sector):
    #    print 'sector.%s' % i
    #print 'dir(sector):', dir(sector)
    
    tags = sector.child_nodes.all()
    #tags = Node.objects.getChildNodes(sector)
    #tags = Node.objects.get_child_nodes(sector)
    return render(request, 'site_admin/view_sector.html', {
        'sector': sector,
        'tags': tags,
    })

@login_required
def list_orphan_tags(request):
    # TODO: check for manager here
    #permissions.require_superuser(request)
    tags = Node.objects.get_orphan_tags()
    return render(request, 'site_admin/list_orphan_tags.html', {
        'tags': tags,
    })

@login_required
def list_tags(request):
    permissions.require_superuser(request)
    
    tags = Node.objects.getTags()
    return render(request, 'site_admin/list_tags.html', {
        'page_title': 'List Tags',
        'tags': tags,
    })

@login_required
def view_tag(request, tagId):
    permissions.require_superuser(request)
    
    tag = Node.objects.get(id=tagId)
    return render(request, 'site_admin/view_tag.html', {
        'tag': tag,
    })

@login_required
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
        
    else:
        # Process the form
        form = CreateTagForm(request.POST)
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
            
            tag.num_related_tags = tag.related_tags.count()
            tag.num_resources = 0
            tag.save()
            
            # Update the related tags counts
            for related_tag in tag.related_tags.all():
                related_tag.num_related_tags = related_tag.related_tags.count()
                related_tag.save()
            
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
                            'sector_names': tag.parent_names(),
                            'num_societies': tag.societies.count(),
                            'num_related_tags': tag.related_tags.count(),
                            'num_filters': tag.filters.count(),
                            'num_resources': tag.resources.count(),
                        },
                    },
                }))
                
            else:
                return HttpResponse("""
                    <script>
                        if (opener && opener.notify) {
                            opener.notify('created_tag', %s);
                        }
                        window.close();
                    </script>
                    <a href="javascript:window.close();">Close window</a>
                    """
                    % json.dumps({
                        'tag': {
                            'id': tag.id,
                            'name': tag.name,
                            'sector_name': tag.parent.name,
                            'name_with_sector': tag.name_with_sector(),
                        }
                    })
                )
        #return HttpResponsePermanentRedirect(reverse('admin_view_tag', args=(tagId,)))
            
    return render(request, 'site_admin/create_tag.html', {
        'form': form,
        'sector': sector,
        'society_id': society_id,
        'add_to_society': add_to_society,
        'done_action': done_action,
        'return_url': return_url,
    })

@login_required
def edit_tag(request, tag_id):
    return_url = request.GET.get('return_url', '')
    #if tag_id is None:
    #    # creating a new tag
    #    form = EditTagForm()
    #else:
    # editing an existing tag
    tag = Node.objects.get(id=tag_id)
    
    form = EditTagForm(initial={
        'id': tag.id,
        'name': tag.name,
        'parents': [parent.id for parent in tag.parents.all()],
        'node_type': tag.node_type.id,
        'societies': tag.societies.all(),
        'filters': [filter.id for filter in tag.filters.all()],
        'related_tags': tag.related_tags.all(),
        'num_resources': tag.num_resources,
    })
    
    form.fields['related_tags'].widget.set_exclude_tag_id(tag.id)
    
    if request.user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
        # Disable certain fields for the society managers
        make_display_only(form.fields['parents'], model=Node)
        make_display_only(form.fields['societies'], model=Society, is_multi_search=True)
        sector_ids = [str(sector.id) for sector in tag.parents.all()]
        form.fields['related_tags'].widget.set_search_url(reverse('ajax_search_tags') + '?filter_sector_ids=' + ','.join(sector_ids))
        
    return render(request, 'site_admin/edit_tag.html', {
        'form': form,
        'return_url': return_url,
    })
        
@login_required
def save_tag(request):
    return_url = request.GET.get('return_url', '')
    form = EditTagForm(request.POST)
    if not form.is_valid():
        if request.user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
            # Disable certain fields for the society managers
            make_display_only(form.fields['parents'], model=Node)
            make_display_only(form.fields['societies'], model=Society, is_multi_search=True)
            tag_id = int(request.POST['id'])
            tag = Node.objects.get(id=tag_id)
            sector_ids = [str(sector.id) for sector in tag.parents.all()]
            form.fields['related_tags'].widget.set_search_url(reverse('ajax_search_tags') + '?filter_sector_ids=' + ','.join(sector_ids))
            
        return render(request, 'site_admin/edit_tag.html', {
            'form': form,
            'return_url': return_url,
        })
    else:
        if form.cleaned_data['id'] is None:
            tag = Node.objects.create()
        else:
            tag = Node.objects.get(id=form.cleaned_data['id'])
        
        tag.name = form.cleaned_data['name']
        tag.parents = form.cleaned_data['parents']
        #tag.node_type = form.cleaned_data['node_type']
        if form.cleaned_data['societies'] is not None:
            tag.societies = form.cleaned_data['societies']
        tag.filters = form.cleaned_data['filters']
        #tag.num_resources = form.cleaned_data['num_resources']
        tag.related_tags = form.cleaned_data['related_tags']
        tag.num_related_tags = tag.related_tags.count()
        tag.save()
        
        # Updated the related tags counts
        for related_tag in tag.related_tags.all():
            related_tag.num_related_tags = related_tag.related_tags.count()
            related_tag.save()
        
        if return_url != '':
            return HttpResponseRedirect(return_url)
        else:
            return HttpResponsePermanentRedirect(reverse('admin_view_tag', args=[tag.id]))
        
@login_required
def search_tags(request):
    permissions.require_superuser(request)
    
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
def users(request):
    permissions.require_superuser(request)
    
    users = User.objects.all()
    return render(request, 'site_admin/users.html', {
        'users': users,
    })

@login_required
def view_user(request, user_id):
    permissions.require_superuser(request)
    
    user = User.objects.get(id=user_id)
    return render(request, 'site_admin/view_user.html', {
        'user': user,
    })
    
@login_required
def edit_user(request, user_id=None):
    permissions.require_superuser(request)
    
    if user_id is None:
        # creating a new user
        form = UserForm()
    else:
        # editing an existing user
        user = User.objects.get(id=user_id)
        form = UserForm(initial={
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
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
def save_user(request):
    permissions.require_superuser(request)
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
            user.is_staff = form.cleaned_data['is_staff']
            user.is_superuser = form.cleaned_data['is_superuser']
            user.societies = form.cleaned_data['societies']
            user.save()
            
            profile = user.get_profile()
            profile.role = form.cleaned_data['role']
            profile.save()
            
            if ask_send_login_info:
                return render(request, 'site_admin/ask_send_login_info.html', {
                    'user': user,
                    'plaintext_password': form.cleaned_data['password1'],
                })
                
            return HttpResponsePermanentRedirect(reverse('admin_users'))
        
    return render(request, 'site_admin/edit_user.html', {
        'user_id': user_id,
        'errors': _errors_to_list(errors),
        'form': form,
    })

@login_required
def delete_user(request, user_id):
    "Deletes a user."
    permissions.require_superuser(request)
    
    User.objects.get(id=user_id).delete()
    return HttpResponsePermanentRedirect(reverse('admin_users'))

@login_required
def delete_users(request):
    """Delete a list of users.
Takes as input a list of user id's in the POST list 'user_ids' (use checkboxes with name="user_ids").
"""
    permissions.require_superuser(request)
    
    user_ids = request.POST.getlist('user_ids')
    for user_id in user_ids:
        User.objects.get(id=user_id).delete()
        
    return HttpResponsePermanentRedirect(reverse('admin_users'))

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
def send_login_info(request, reason):
    permissions.require_superuser(request)
    
    user_ids = request.POST.getlist('user_ids')
    plaintext_passwords = request.POST.getlist('plaintext_passwords')
    
    for user_id, plaintext_password in zip(user_ids, plaintext_passwords):
        user = User.objects.get(id=user_id)
        _send_user_login_info_email(request, user, plaintext_password, reason)
    
    return HttpResponseRedirect(reverse('admin_users'))

@login_required
def societies(request):
    permissions.require_superuser(request)
    
    societies = Society.objects.getForUser(request.user)
    return render(request, 'site_admin/societies.html', {
        'societies': societies,
    })

@login_required
def view_society(request, society_id):
    permissions.require_superuser(request)
    
    society = Society.objects.get(id=society_id)
    return render(request, 'site_admin/view_society.html', {
        'society': society,
    })

def _get_paged_tags(society, tag_sort, tag_page):
    _TAGS_PER_PAGE = 20
    
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
    
    elif tag_sort == 'num_related_tags_ascending':
        tags = society.tags.extra(select={
            'num_related_tags': 'SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id',
        }, order_by=[
            'num_related_tags',
        ])
    elif tag_sort == 'num_related_tags_descending':
        tags = society.tags.extra(select={
            'num_related_tags': 'SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id',
        }, order_by=[
            '-num_related_tags',
        ])
    
    else:
        raise Exception('Unknown tag_sort "%s"' % tag_sort)
    
    num_tags = tags.count()
    num_tag_pages = int(math.ceil(num_tags / float(_TAGS_PER_PAGE)))
    
    tag_start_count = (tag_page-1) * _TAGS_PER_PAGE
    tag_end_count = (tag_page) * _TAGS_PER_PAGE
    tags = tags[tag_start_count:tag_end_count]
    
    return (tags, num_tag_pages)

@login_required
def manage_society(request, society_id):
    try:
        permissions.require_society_user(request, society_id)
    except Exception, e:
        # Give a friendly error page with a link to the correct home page
        # TODO: Better fix for this later
        return HttpResponseRedirect(reverse('permission_denied'))
    
    _RESOURCES_PER_PAGE = 50
    
    # Default to name/ascending resource_sort
    resource_sort = request.GET.get('resource_sort', 'priority_ascending')
    resource_page = int(request.GET.get('resource_page', 1))
    
    # Default to name/ascending tag_sort
    tag_sort = request.GET.get('tag_sort', 'name_ascending')
    tag_page = int(request.GET.get('tag_page', 1))
    
    society = Society.objects.get(id=society_id)
    
    form = ManageSocietyForm(initial={
        'tags': society.tags.all(),
        #'resources': society.resources.all(),
    })
    
    form.fields['tags'].widget.set_society_id(society_id)
    
    if resource_sort == 'name_ascending':
        resources1 = society.resources.order_by('name')
    elif resource_sort == 'name_descending':
        resources1 = society.resources.order_by('-name')
    
    elif resource_sort == 'ieee_id_ascending':
        
        # Ignore warning about turning non-numeric value into an integer ("Truncated incorrect INTEGER value: 'xxxx'")
        warnings.filterwarnings('ignore', '^Truncated incorrect INTEGER value:.+')
        
        resources1 = society.resources.extra(select={
            'ieee_id_num': 'SELECT CAST(ieee_id AS SIGNED INTEGER)',
        }, order_by=[
            'ieee_id_num',
            'ieee_id',
            'name',
        ])
        
    elif resource_sort == 'ieee_id_descending':
        
        # Ignore warning about turning non-numeric value into an integer ("Truncated incorrect INTEGER value: 'xxxx'")
        warnings.filterwarnings('ignore', '^Truncated incorrect INTEGER value:.+')
        
        resources1 = society.resources.extra(select={
            'ieee_id_num': 'SELECT CAST(ieee_id AS SIGNED INTEGER)',
        }, order_by=[
            '-ieee_id_num',
            '-ieee_id',
            '-name',
        ])
    
    elif resource_sort == 'resource_type_ascending':
        resources1 = society.resources.order_by('resource_type', 'standard_status', 'name')
    elif resource_sort == 'resource_type_descending':
        resources1 = society.resources.order_by('-resource_type', '-standard_status', '-name')
    
    elif resource_sort == 'url_ascending':
        resources1 = society.resources.order_by('url', 'name')
    elif resource_sort == 'url_descending':
        resources1 = society.resources.order_by('-url', '-name')
    
    elif resource_sort == 'num_tags_ascending':
        resources1 = society.resources.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_tags',
        ])
    elif resource_sort == 'num_tags_descending':
        resources1 = society.resources.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_tags',
        ])
    
    elif resource_sort == 'num_societies_ascending':
        resources1 = society.resources.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_societies',
        ])
    elif resource_sort == 'num_societies_descending':
        resources1 = society.resources.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_societies',
        ])
    
    # NOTE: These are reversed, since that seems more intutive
    elif resource_sort == 'priority_ascending':
        resources1 = society.resources.order_by('-priority_to_tag', 'name')
    elif resource_sort == 'priority_descending':
        resources1 = society.resources.order_by('priority_to_tag', '-name')
    
    elif resource_sort == 'description_ascending':
        resources1 = society.resources.order_by('description', 'name')
    elif resource_sort == 'description_descending':
        resources1 = society.resources.order_by('-description', '-name')
    
    else:
        raise Exception('Unknown resource_sort "%s"' % resource_sort)
    
    # Limit search results to one page
    num_resources = resources1.count()
    num_resource_pages = int(math.ceil(num_resources / float(_RESOURCES_PER_PAGE)))
    
    # NOTE: resource_page starts at 1, not 0
    resource_start_count = (resource_page-1) * _RESOURCES_PER_PAGE
    resource_end_count = (resource_page) * _RESOURCES_PER_PAGE
    resources1 = resources1[resource_start_count:resource_end_count]
    resource_page_url = reverse('admin_manage_society', args=[society.id]) + '?resource_sort=' + quote(resource_sort) + '&amp;resource_page={{ page }}#tab-resources-tab'
    
    (tags, num_tag_pages) = _get_paged_tags(society, tag_sort, tag_page)
    tag_page_url = reverse('admin_manage_society', args=[society.id]) + '?tag_sort=' + quote(tag_sort) + '&amp;tag_page={{ page }}#tab-tags-tab'
    
    # Add the resource row count to the resource object
    #count = resource_start_count
    #for resource1 in resources1:
    #    resource1.count = count+1
    #    count += 1 
    
    # For each resource, get a list of society abbreviations in alphabetical order
    resources = []
    for resource in resources1:
        resource.society_abbreviations = [society1.abbreviation for society1 in resource.societies.order_by('abbreviation')]
        resources.append(resource)
    
    tags_tab_url = reverse('admin_manage_society', args=[society_id]) + '#tab-tags-tab'
    
    return render(request, 'site_admin/manage_society.html', {
        'society': society,
        'form': form,
        
        'resources': resources,
        'resource_sort': resource_sort,
        'resource_page': resource_page,
        'num_resources': num_resources,
        'resource_page_url': resource_page_url,
        'num_resource_pages': num_resource_pages,
        
        'tags': tags,
        'tags_tab_url': tags_tab_url,
        'tag_sort': tag_sort,
        'tag_page': tag_page,
        'num_tag_pages': num_tag_pages,
        'tag_page_url': tag_page_url,
        
        'DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB': settings.DEBUG_ENABLE_MANAGE_SOCIETY_HELP_TAB,
    })

@login_required
def manage_society_tags_table(request, society_id, tag_sort, tag_page):
    society = Society.objects.get(id=society_id)
    tag_page = int(tag_page)
    (tags, num_tag_pages) = _get_paged_tags(society, tag_sort, tag_page)
    tag_page_url = reverse('admin_manage_society', args=[society.id]) + '?tag_sort=' + quote(tag_sort) + '&amp;tag_page={{ page }}#tab-tags-tab'
    
    return render(request, 'site_admin/manage_society_tags_table.html', {
        'tag_sort': tag_sort,
        'tag_page': tag_page,
        'num_tag_pages': num_tag_pages,
        'society': society,
        'tags': tags,
        'tag_page_url': tag_page_url,
    })

@login_required
def edit_society(request, society_id=None):
    permissions.require_superuser(request)
    
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
def save_society(request):
    permissions.require_superuser(request)
    
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
def delete_society(request, society_id):
    permissions.require_superuser(request)
    
    Society.objects.get(id=society_id).delete()
    return HttpResponsePermanentRedirect(reverse('admin_societies'))

@login_required
def search_societies(request):
    permissions.require_superuser(request)
    
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
def list_resources(request, type1):
    permissions.require_superuser(request)
    
    if type1 == 'conferences':
        type1 = 'conference'
    elif type1 == 'standards':
        type1 = 'standard'
    elif type1 == 'periodicals':
        type1 = 'periodical'
        
    resource_type = ResourceType.objects.getFromName(type1)
    resources = Resource.objects.filter(resource_type=resource_type)
    return render(request, 'site_admin/list_resources.html', {
        'resource_type': resource_type,
        'resources': resources,
    })

@login_required
def view_resource(request, resource_id):
    if 'return_url' not in request.GET:
        raise Exception('query variable "return_url" not found')
        
    return_url = request.GET['return_url']
    resource = Resource.objects.get(id=resource_id)
    return render(request, 'site_admin/view_resource.html', {
        'return_url': return_url,
        'resource': resource,
    })

@login_required
def edit_resource(request, resource_id=None):
    if 'return_url' not in request.GET:
        raise Exception('query variable "return_url" not found')
    
    return_url = request.GET['return_url']
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
            make_display_only(form.fields['societies'], is_multi_search=True)
        
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
            'keywords': resource.keywords,
            'standard_status': resource.standard_status,
        })
        
        if society_id != '':
            form.fields['nodes'].widget.set_search_url(reverse('ajax_search_tags') + '?society_id=' + society_id)
            form.fields['nodes'].widget.set_society_id(society_id)
        
        # Disable edit resource form fields for societies
        if not request.user.is_superuser:
            make_display_only(form.fields['name'])
            make_display_only(form.fields['societies'], is_multi_search=True)
            make_display_only(form.fields['ieee_id'])
            make_display_only(form.fields['keywords'])
            make_display_only(form.fields['standard_status'])
        
    return render(request, 'site_admin/edit_resource.html', {
        'return_url': return_url,
        'society_id': society_id,
        'resource': resource,
        'form': form,
    })

@login_required
def save_resource(request):
    if 'return_url' not in request.GET:
        raise Exception('Query variable "return_url" not found')
    return_url = request.GET['return_url']
    
    if 'id' not in request.POST:
        form = CreateResourceForm(request.POST)
    else:
        form = EditResourceForm(request.POST)
    
    if not form.is_valid():
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
        })
    else:
        if 'id' in form.cleaned_data:
            resource = Resource.objects.get(id=form.cleaned_data['id'])
        else:
            resource = Resource.objects.create(
                resource_type=form.cleaned_data['resource_type']
            )
        
        # Need to update these node totals later (in case the user has removed one from this resource)
        old_nodes = resource.nodes.all()
        
        resource.name = form.cleaned_data['name']
        resource.ieee_id = form.cleaned_data['ieee_id']
        resource.description = form.cleaned_data['description']
        resource.url = form.cleaned_data['url']
        resource.nodes = form.cleaned_data['nodes']
        if form.cleaned_data['societies'] is not None:
            resource.societies = form.cleaned_data['societies']
        resource.priority_to_tag = form.cleaned_data['priority_to_tag']
        resource.keywords = form.cleaned_data['keywords']
        if 'standard_status' in request.POST:
            resource.standard_status = form.cleaned_data['standard_status']
        resource.save()
        
        # Add all resource tags to the owning societies
        for society in resource.societies.all():
            for node in resource.nodes.all():
                society.tags.add(node)
            society.save()
        
        # Update the node totals
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
        else:
            return HttpResponsePermanentRedirect(return_url)

@login_required
def delete_resource(request, resource_id):
    permissions.require_superuser(request)
    
    old_nodes = resource.nodes
    Resource.objects.get(id=resource_id).delete()
    _update_node_totals(old_nodes)
    return HttpResponsePermanentRedirect(reverse('admin_list_resources'))

@login_required
def search_resources(request):
    permissions.require_superuser(request)
    
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
    tags = Node.objects.searchTagsByNameSubstring(search_for, sector_ids, exclude_tag_id)
    
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
                'sector_names': tag.parent_names(),
                'num_societies': tag.societies.count(),
                'num_related_tags': tag.related_tags.count(),
                'num_filters': tag.filters.count(),
                'num_resources': tag.resources.count(),
                'societies': societies,
            })
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")

@login_required
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
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")

@login_required
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
    
    return HttpResponse(json.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")
    
@login_required
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
