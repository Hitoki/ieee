import codecs
import csv
import hashlib
import random
import re
import string
import time
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.contrib.auth.models import User
from django.utils import simplejson as json

from ieeetags import settings
from ieeetags.util import *
from ieeetags.models import Node, NodeType, Permission, Resource, ResourceType, Society, Filter, Profile, get_user_from_username, get_user_from_email
from ieeetags.logger import log
from ieeetags.views import render
from ieeetags.widgets import DisplayOnlyWidget
from forms import *
from widgets import make_display_only

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
                    from datetime import datetime
                    date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
        except Exception:
            version = 'UNKNOWN'
            date = ''
            
        #print 'version:', version
        #print 'date:', date
    
    return version, date

def _update_node_totals(nodes):
    for node in nodes:
        node.num_resources = len(node.resources.all())
        node.save()
    
def _update_tag_related_sectors(tag, recurse=True):
    same_name_tags = Node.objects.getTagsByName(tag.name)
    num_related_sectors = len(same_name_tags.all())-1
    
    # Update this tag's counts
    tag.num_related_sectors = num_related_sectors
    tag.related_sectors = [same_name_tag.parent for same_name_tag in same_name_tags.exclude(id=tag.id)]
    tag.save()
    
    # Update all other same-name tags' counts
    for tag2 in same_name_tags:
        tag2.num_related_sectors = num_related_sectors
        tag2.related_sectors = [same_name_tag.parent for same_name_tag in same_name_tags.exclude(id=tag2.id)]
        tag2.save()

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

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
    else:
        form = LoginForm()
    if not form.is_valid():
        return render(request, 'site_admin/login.html', {
            'form': form,
        })
    else:
        user = auth.authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
        if user is None:
            return render(request, 'site_admin/login.html', {
                'error': 'Invalid login, please try again.',
                'form': form,
            })
        else:
            auth.login(request, user)
            return HttpResponsePermanentRedirect(reverse('admin_home'))

def logout(request):
    auth.logout(request)
    return HttpResponsePermanentRedirect(reverse('admin_home'))

def _send_password_reset_email(request, user):
    if user.get_profile().reset_key is None:
        profile = user.get_profile()
        
        hash = hashlib.md5()
        hash.update(str(random.random()))
        hash = hash.hexdigest()
        
        profile.reset_key = hash
        profile.save()
    
    abs_reset_url = request.build_absolute_uri(reverse('password_reset', args=[user.id, user.get_profile().reset_key]))
    
    subject = 'IEEE Technology Navigator: password reset confirmation'
    message = """You have requested to reset your password for the IEEE Technology Navigator.
    
To complete this request and reset your password, please click on the link below:
%s

If you did not request this password reset, simple ignore this email.
""" % (abs_reset_url)
    
    print 'settings.DEFAULT_FROM_EMAIL:', settings.DEFAULT_FROM_EMAIL
    print 'user.email:', user.email
    print 'subject:', subject
    print 'message:', message
    print 'Sending email...'
    print ''

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

def forgot_password(request):
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
                    _send_password_reset_email(request, user)
                    return HttpResponseRedirect(reverse('forgot_password_confirmation'))
                    
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
    })

def forgot_password_confirmation(request):
    return render(request, 'site_admin/forgot_password_confirmation.html')

def password_reset(request, user_id, reset_key):
    user = User.objects.get(id=user_id)
    profile = user.get_profile()
    #print 'password_reset()'
    #print '  user_id:', user_id
    #print '  user.get_profile().reset_key:', user.get_profile().reset_key
    #print '  reset_key:', reset_key
    
    if profile.reset_key is not None and reset_key == profile.reset_key:
        # Got the right reset key
        error = ''
        if request.method == 'GET':
            form = ResetPasswordForm()
        else:
            form = ResetPasswordForm(request.POST)
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
def home(request):
    role = request.user.get_profile().role
    
    if role == Profile.ROLE_ADMIN:
        version, date = _get_version()
        return render(request, 'site_admin/admin_home.html', {
            'version': version,
            'date': date,
        })
        
    elif role == Profile.ROLE_SOCIETY_MANAGER:
        hash = request.GET.get('hash', '')
        
        # Only one society, just redirect to that view page
        if len(request.user.societies.all()) == 1:
            return HttpResponseRedirect(reverse('admin_manage_society', args=[request.user.societies.all()[0].id]) + hash)
        
        # Has more than one society, show list of societies
        elif len(request.user.societies.all()) > 1:
            #return HttpResponseRedirect(reverse('admin_societies'))
            return HttpResponseRedirect(reverse('admin_home_societies_list') + hash)
        
        else:
            raise Exception('User is a society manager but is not assigned to any societies.')
        
    else:
        raise Exception('Unknown role %s' % role)

@login_required
def home_societies_list(request):
    societies = Society.objects.getForUser(request.user)
    return render(request, 'site_admin/home_societies_list.html', {
        'societies': societies,
    })


@login_required
def update_tag_counts(request):
    start = time.time()
    numTags = Node.objects.updateTagCounts()
    return render(request, 'site_admin/update_tag_counts.html', {
        'pageTime': time.time()-start,
        'numTags': numTags,
    })


def split_no_empty(string, char):
    "Just like string.split(), except that an empty string results in an empty list []."
    if string.strip() == '':
        return []
    else:
        return string.split(char)

@login_required
def import_tags(request):
    log('import_tags()')
    start = time.time()
    
    filename = relpath(__file__, '../data/comsoc - tags.csv')
    log('  filename: %s' % filename)
    
    # Delete all existing tags
    Node.objects.getTags().delete()
    
    file = codecs.open(filename, 'r', 'utf8')
    # Skip the UTF-8 BOM
    strip_bom(file)
    # Use a unicode csv reader:
    reader = _unicode_csv_reader(file)
    reader.next()
    
    # DEBUG: For comsoc only:
    comsoc = Society.objects.all()[0]
    
    row_count = 0
    tags_created = 0
    related_tags_assigned = 0
    for row in reader:
        # Tag,Sectors,Filters,Related Tags
        tag_name, sector_names, filter_names, related_tag_names = row
        tag_name = tag_name.strip()
        sector_names = [sector_name.strip() for sector_name in split_no_empty(sector_names, ',')]
        filter_names = [filter_name.strip() for filter_name in split_no_empty(filter_names, ',')]
        
        sectors = [Node.objects.getSectorByName(sector_name) for sector_name in sector_names]
        filters = [Filter.objects.getFromName(filter_name) for filter_name in filter_names]
        
        for sector in sectors:
            tag = Node.objects.create_tag(
                name=tag_name,
                parent=sector,
                #filters=filters,
            )
            tag.filters = filters
            
            # DEBUG: For comsoc demo, assign all tags to COMSOC society
            tag.societies.add(comsoc)
            tag.save()
            tags_created += 1
            
        row_count += 1
        if not row_count % 10:
            print '  Parsing row %d' % row_count
    file.close()
    
    # Now reopen the file to parse for related tags
    file = codecs.open(filename, 'r', 'utf8')
    # Skip the UTF-8 BOM
    strip_bom(file)
    # Use a unicode csv reader:
    reader = _unicode_csv_reader(file)
    reader.next()
    row_count = 0
    for row in reader:
        # Tag,Sectors,Filters,Related Tags
        tag_name, sector_names, filter_names, related_tag_names = row
        tag_name = tag_name.strip()
        sector_names = [sector_name.strip() for sector_name in split_no_empty(sector_names, ',')]
        related_tag_names = [related_tag_name.strip() for related_tag_name in split_no_empty(related_tag_names, ',')]
        
        sectors = [Node.objects.getSectorByName(sector_name) for sector_name in sector_names]
        
        for sector in sectors:
            tag = Node.objects.getTagByName(sector, tag_name)
            related_tags = []
            for related_tag_name in related_tag_names:
                related_tags.extend(Node.objects.getTagsByName(related_tag_name))
            tag.related_tags = related_tags
            related_tags_assigned += len(related_tags)
            tag.save()
            
        #row_count += 1
        #if not row_count % 10:
        #    print '  Parsing row %d' % row_count
    file.close()
    
    return render(request, 'site_admin/import_tags.html', {
        'row_count': row_count,
        'tags_created': tags_created,
        'related_tags_assigned': related_tags_assigned,
        'page_time': time.time()-start,
    })
    
@login_required
def import_societies_and_tags(request):
    log('import_societies_and_tags()')
    start = time.time()
    
    filename = relpath(__file__, '../data/2009-03-15 societies and tags.csv')
    #filename = relpath(__file__, '../data/2009-03-15 societies and tags - short.csv')
    log('  filename: %s' % filename)
    
    # Delete all existing societies
    Society.objects.all().delete()
    
    # Delete all existing tags
    Node.objects.getTags().delete()
    
    file = codecs.open(filename, 'r', 'utf8')
    # Skip the UTF-8 BOM
    strip_bom(file)
    #reader = csv.reader(file)
    # Use a unicode csv reader:
    reader = _unicode_csv_reader(file)
    row_count = 0
    societies_created = 0
    tags_created = 0
        
    reader.next()
    
    tag_type = NodeType.objects.getFromName('tag')
    
    for row in reader:
        society_name, abbreviation, url, sector_name, tags1, tags2, tags3 = row
        
        society_name = society_name.strip()
        
        # Make sure the society name field does not contain a redundant acronym (there is already have an acronym field)
        matches = re.match(r'^(.+) \((.+)\)$', society_name)
        if matches is not None:
            society_name = matches.group(1)
        #log('society name: %s' % society_name)
        
        (society, created) = Society.objects.get_or_create(
            name=society_name,
        )
        society.abbreviation = abbreviation
        society.url = url
        society.save()
        
        if created:
            societies_created += 1
        
        sector = Node.objects.get_sector_by_name(sector_name)
        
        # Combine all the lists of tags
        tag_names = []
        if tags1.split(', ') is not None:
            tag_names.extend(tags1.split(','))
        if tags2.split(', ') is not None:
            tag_names.extend(tags2.split(','))
        if tags3.split(', ') is not None:
            tag_names.extend(tags3.split(','))
        
        for tag_name in tag_names:
            tag_name = string.capwords(tag_name).strip()
            if tag_name != '':
                
                (tag, created) = Node.objects.get_or_create(
                    name=tag_name,
                    parent=sector,
                    node_type=tag_type,
                )
                # Associate tag with society
                tag.societies.add(society)
                if created:
                    #log('Created tag "%s"' % tag_name)
                    #tag.filters = []
                    tag.num_resources = 0
                    tag.num_related_sectors = 0
                    tags_created += 1
                tag.save()
                
        row_count += 1
        if not row_count % 10:
            print '  Parsing row %d' % row_count
        
    file.close()
    
    return render(request, 'site_admin/import_societies_and_tags.html', {
        'row_count': row_count,
        'societies_created': societies_created,
        'tags_created': tags_created,
        'page_time': time.time()-start,
    })

@login_required
def import_conferences(request):
    start = time.time()
    
    #log('import_conferences()')
    
    row_count = 0
    duplicate_conferences = 0
    conferences_added = 0
    societies_assigned = 0
    invalid_societies = 0
    
    conference_type = ResourceType.objects.getFromName(ResourceType.CONFERENCE)
    
    # Delete all conferences!
    Resource.objects.filter(resource_type=conference_type).delete()
    
    for filename in [
        #'conferences/2009-03-13 - conference_list - short.txt',
        'conferences/2009-03-13 - conference_list.txt',
    ]:
    
        filename = relpath(__file__, '../data/' + filename)
        print 'filename:', filename
        
        file = codecs.open(filename, 'r', 'utf8')
        
        # Skip the UTF-8 BOM
        strip_bom(file)
        
        # Skip the first line
        file.readline()
        
        last_line = None
        
        for line in file:
            
            #print 'line:', line
            #print ''
            
            values = line.split('|')
            
            if len(values) < 5:
                # Found the wrong number of columns, check for multi line inputs
                while len(values) < 5:
                    # Parse the next line
                    line = file.readline()
                    bits = line.split('|')
                    # Append the next segment to the last field
                    values[len(values)-1] += bits[0]
                    # If there were more than one field on this line, add those fields to the list
                    if len(bits) > 1:
                        values.extend(bits[1:])
            
            ieee_id, year, title, description, url, society_names = values
            year = int(year)
            assert title.strip() != ''
            
            societies = []
            #print 'society_names:'
            for society_name in society_names.split(','):
                if society_name.strip() != '':
                    parts = society_name.strip().split(' - ')
                    name = parts[0]
                    #print '  name:', name
                    # Remove the ' Society' part from the name
                    if name[-8:] == ' Society':
                        name = name[:-8]
                        #print '  -name:', name
                    
                    society = Society.objects.getFromName(name)
                    #print '  society:', society
                    if society is None:
                        #log('Society "%s" not found' % name)
                        invalid_societies += 1
                    else:
                        societies_assigned += 1
                        societies.append(society)
            
            if True:
                num_existing = len(Resource.objects.filter(resource_type=conference_type, ieee_id=ieee_id).all())
                if num_existing > 0:
                    #log('  DUPLICATE: conference "%s" already exists.' % title)
                    duplicate_conferences += 1
                else:
                    ##log('  Adding conference "%s"' % name)
                    conference = Resource.objects.create(
                        resource_type=conference_type,
                        ieee_id=ieee_id,
                        name=title,
                        description=description,
                        url=url,
                        year=year,
                    )
                    conference.societies = societies
                    conference.save()
                    conferences_added += 1
                    
            if not row_count % 200:
                print '  Reading row %d' % row_count
                
            last_line = line
            row_count += 1
            
            
        file.close()
    
    return render(request, 'site_admin/import_conferences.html', {
        'page_time': time.time()-start,
        'row_count': row_count,
        'duplicate_conferences': duplicate_conferences,
        'conferences_added': conferences_added,
        'societies_assigned': societies_assigned,
        'invalid_societies': invalid_societies,
    })

def _import_resources(type, filename):
    log('_import_resources()')
    log('  filename: %s' % filename)
    file = open(filename)
    reader = csv.reader(file)
    reader.next()
    
    rowCount = 0
    resourcesAdded = 0
    
    resourceType = ResourceType.objects.getFromName(type)
    for row in reader:
        (resourceName, sectorNames, tagNames, societyNames, description, url) = row
        resourceName = string.capwords(resourceName)
        log('  Resource name "%s"' % resourceName)
        
        resource = Resource.objects.create(
            resource_type=resourceType,
            name=resourceName,
            description=description,
            url=url,
        )
        
        # TODO: randomly assigning tag here
        #resource.nodes.add(Node.objects.getRandomTag())
        
        if societyNames != '':
            for societyName in societyNames.split(', '):
                society = Society.objects.getFromName(societyName)
                if society is None:
                    log('  Error: bad society name "%s"' % societyName)
                else:
                    log('  Associating resource with society "%s"' % societyName)
                    resource.societies.add(society)
        
        #log('  Number of societies: %d' % len(resource.societies.all()))
        
        # DEBUG: Make sure this resource has at least one randomly-chosen society
        if len(resource.societies.all()) == 0:
            society = Society.objects.getRandom()
            log('  Assigning resource to random society "%s"' % society.name)
            resource.societies.add(society)
        
        resource.save()
        resourcesAdded += 1
        
        rowCount += 1
        
    file.close()
    
    return (rowCount, resourcesAdded)

@login_required
def import_resources(request):
    log('admin_import_resources()')
    
    start = time.time()
    
    # Delete all existing resources
    Resource.objects.all().delete()
    
    # DEBUG: use a small import file for testing
    if False:
        filename = relpath(__file__, '../data/conferences.short.csv')
        #filename = relpath(__file__, '../data/conferences.csv')
        (conferenceRowCount, conferenceCount) = _import_resources('conference', filename)
        
        return render(request, 'site_admin/import_resources.html', {
            'conferenceRowCount': conferenceRowCount,
            'conferenceCount': conferenceCount,
            'pageTime': time.time()-start,
        })
    else:

        # Replaced by newer conferences import files
        #filename = relpath(__file__, '../data/conferences.csv')
        #(conferenceRowCount, conferenceCount) = _import_resources('conference', filename)
        
        filename = relpath(__file__, '../data/experts.csv')
        (expertRowCount, expertCount) = _import_resources('expert', filename)
        
        filename = relpath(__file__, '../data/periodicals.csv')
        (periodicalRowCount, periodicalCount) = _import_resources('periodical', filename)
        
        filename = relpath(__file__, '../data/standards.csv')
        (standardRowCount, standardCount) = _import_resources('standard', filename)

        return render(request, 'site_admin/import_resources.html', {
            'conferenceRowCount': conferenceRowCount,
            'conferenceCount': conferenceCount,
            'expertRowCount': expertRowCount,
            'expertCount': expertCount,
            'periodicalRowCount': periodicalRowCount,
            'periodicalCount': periodicalCount,
            'standardRowCount': standardRowCount,
            'standardCount': standardCount,
            'pageTime': time.time()-start,
        })

@login_required
def assign_filters(request):
    start = time.time()
    
    tagsAssignedTo = 0
    filtersAssigned = 0
    
    filters = [filter for filter in Filter.objects.all()]
    
    tags = Node.objects.getTags()
    #print 'len(tags):', len(tags)
    
    for tag in tags:
        filters1 = _random_slice_list(filters, 1, 4)
        for filter in filters1:
            tag.filters.add(filter)
            filtersAssigned += 1
        tagsAssignedTo += 1
            
    return render(request, 'site_admin/assign_filters.html', {
        'pageTime': time.time()-start,
        'tagsAssignedTo': tagsAssignedTo,
        'filtersAssigned': filtersAssigned,
    })

@login_required
def assign_related_tags(request):
    start = time.time()
    
    tag_count = 0
    
    # First, delete all related tags
    tags = Node.objects.getTags()
    for tag in tags:
        tag.related_tags = []
        tag.save()
    
    # Now assign related tags
    tags = Node.objects.getTags()
    for tag in tags:
        tag.related_tags = Node.objects.get_random_related_tags(tag, 3)
        tag.save()
        
        tag_count += 1
        if not tag_count % 10:
            print '  Tag %d' % tag_count
        
        if tag_count > 100:
            break
    
    # Now update the tag counts
    tags = Node.objects.getTags()
    for tag in tags:
        tag.num_related_tags = len(tag.related_tags.all())
        tag.save()
            
    return render(request, 'site_admin/assign_related_tags.html', {
        'page_time': time.time()-start,
        'tag_count': tag_count,
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
def assign_resources(request):
    start = time.time()
    
    print 'assign_resources()'
    
    if True:
        # First, disassociate any resources
        print '  removing resources'
        tags = Node.objects.getTags()
        tag_count = 0
        for tag in tags:
            tag.resources = []
            tag.save()
            tag_count += 1
            if not tag_count % 50:
                print '  Tag %d' % tag_count
    
    resources = Resource.objects.all()
    
    print '  assigning resources'
    # Now assign resources
    tags = Node.objects.getTags()
    tag_count = 0
    resources_assigned = 0
    for tag in tags:
        #print '    tag.name:', tag.name
        #print '    count = random.randint(1, 5)'
        count = random.randint(1, 12)
        #print '    tag.resources = Resource.objects.get_random(count)'
        #tag.resources = Resource.objects.get_random(count)
        
        #print '    tag.resources = _get_random_from_sequence(resources, count)'
        tag.resources = _get_random_from_sequence(resources, count)
        
        #print '    tag.num_resources = len(tag.resources.all())'
        tag.num_resources = len(tag.resources.all())
        #print '    tag.save()'
        tag.save()
        #print '    resources_assigned += count'
        resources_assigned += count
        
        tag_count += 1
        if not tag_count % 10:
            print '  Tag %d' % tag_count
    
    avg_resources_per_tag = resources_assigned / tag_count
    
    return render(request, 'site_admin/assign_resources.html', {
        'page_time': time.time()-start,
        'tag_count': tag_count,
        'resources_assigned': resources_assigned,
        'avg_resources_per_tag': avg_resources_per_tag,
    })

@login_required
def list_sectors(request):
    sectors = Node.objects.getSectors()
    return render(request, 'site_admin/list_sectors.html', {
        'sectors': sectors,
    })

@login_required
def view_sector(request, sectorId):
    sector = Node.objects.get(id=sectorId)
    tags = Node.objects.getChildNodes(sector)
    return render(request, 'site_admin/view_sector.html', {
        'sector': sector,
        'tags': tags,
    })

@login_required
def list_tags(request):
    tags = Node.objects.getTags()
    return render(request, 'site_admin/list_tags.html', {
        'tags': tags,
    })

@login_required
def view_tag(request, tagId):
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
    
    if request.method == 'GET':
        # Show the create tag form
        form = CreateTagForm(initial={
            'sector': sector_id,
        })
        
    else:
        # Process the form
        form = CreateTagForm(request.POST)
        if form.is_valid():
            tag = Node.objects.create(
                name=form.cleaned_data['name'],
                parent=form.cleaned_data['sector'],
                node_type=NodeType.objects.getFromName(NodeType.TAG),
            )
            
            if society_id != '':
                society = Society.objects.get(id=int(society_id))
                tag.societies = [society]
            
            tag.filters = form.cleaned_data['filters']
            tag.related_tags = form.cleaned_data['related_tags']
            
            tag.num_related_tags = len(tag.related_tags.all())
            tag.num_resources = 0
            tag.save()
            
            # Update the related tags counts
            for related_tag in tag.related_tags.all():
                related_tag.num_related_tags = len(related_tag.related_tags.all())
                related_tag.save()
            
            # Update the related sectors
            _update_tag_related_sectors(tag)
            
            if return_url != '':
                return HttpResponseRedirect(return_url)
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
        'parent': tag.parent.id,
        'node_type': tag.node_type.id,
        'societies': tag.societies.all(),
        'filters': [filter.id for filter in tag.filters.all()],
        'related_tags': tag.related_tags.all(),
        'num_resources': tag.num_resources,
        'related_sectors': tag.related_sectors.all(),
    })
    
    if request.user.get_profile().role == Profile.ROLE_SOCIETY_MANAGER:
        # Disable certain fields for the society managers
        make_display_only(form.fields['parent'], model=Node)
        make_display_only(form.fields['name'])
        make_display_only(form.fields['societies'], model=Society, is_multi_search=True)
        make_display_only(form.fields['num_resources'])
        make_display_only(form.fields['related_sectors'], model=Node)
        
    return render(request, 'site_admin/edit_tag.html', {
        'form': form,
        'return_url': return_url,
    })
        
@login_required
def save_tag(request):
    return_url = request.GET.get('return_url', '')
    form = EditTagForm(request.POST)
    if not form.is_valid():
        return render(request, 'site_admin/edit_tag.html', {
            'form': form,
        })
    else:
        if form.cleaned_data['id'] is None:
            tag = Node.objects.create()
        else:
            tag = Node.objects.get(id=form.cleaned_data['id'])
        
        tag.name = form.cleaned_data['name']
        tag.parent = form.cleaned_data['parent']
        #tag.node_type = form.cleaned_data['node_type']
        if form.cleaned_data['societies'] is not None:
            tag.societies = form.cleaned_data['societies']
        tag.filters = form.cleaned_data['filters']
        tag.num_resources = form.cleaned_data['num_resources']
        tag.related_tags = form.cleaned_data['related_tags']
        tag.num_related_tags = len(tag.related_tags.all())
        tag.save()
        
        # Updated the related tags counts
        for related_tag in tag.related_tags.all():
            related_tag.num_related_tags = len(related_tag.related_tags.all())
            related_tag.save()
        
        # Update the related sectors
        _update_tag_related_sectors(tag)
        
        if return_url != '':
            return HttpResponseRedirect(return_url)
        else:
            return HttpResponsePermanentRedirect(reverse('admin_view_tag', args=[tag.id]))
        
@login_required
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
def users(request):
    users = User.objects.all()
    return render(request, 'site_admin/users.html', {
        'users': users,
    })

@login_required
def view_user(request, user_id):
    user = User.objects.get(id=user_id)
    return render(request, 'site_admin/view_user.html', {
        'user': user,
    })
    
@login_required
def edit_user(request, user_id=None):
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
        
@login_required
def save_user(request):
    form = UserForm(request.POST)
    if not form.is_valid():
        return render(request, 'site_admin/edit_user.html', {
            'form': form,
        })
    else:
        if form.cleaned_data['id'] is None:
            user = User.objects.create()
        else:
            user = User.objects.get(id=form.cleaned_data['id'])
        user.username = form.cleaned_data['username']
        user.first_name = form.cleaned_data['first_name']
        user.last_name = form.cleaned_data['last_name']
        user.email = form.cleaned_data['email']
        user.is_staff = form.cleaned_data['is_staff']
        user.is_superuser = form.cleaned_data['is_superuser']
        user.societies = form.cleaned_data['societies']
        user.save()
        
        profile = user.get_profile()
        profile.role = form.cleaned_data['role']
        profile.save()
        
        return HttpResponsePermanentRedirect(reverse('admin_users'))

@login_required
def delete_user(request, user_id):
    User.objects.get(id=user_id).delete()
    return HttpResponsePermanentRedirect(reverse('admin_users'))

@login_required
def societies(request):
    societies = Society.objects.getForUser(request.user)
    return render(request, 'site_admin/societies.html', {
        'societies': societies,
    })

@login_required
def view_society(request, society_id):
    society = Society.objects.get(id=society_id)
    return render(request, 'site_admin/view_society.html', {
        'society': society,
    })

@login_required
def manage_society(request, society_id):
    sort = request.GET.get('sort', '')
    society = Society.objects.get(id=society_id)
    
    #print 'sort:', sort
    
    form = ManageSocietyForm(initial={
        'tags': society.tags.all(),
        'resources': society.resources.all(),
    })
    
    if sort == 'name_ascending':
        resources1 = society.resources.order_by('name')
    elif sort == 'name_descending':
        resources1 = society.resources.order_by('-name')
    
    elif sort == 'ieee_id_ascending':
        resources1 = society.resources.order_by('ieee_id', 'name')
    elif sort == 'ieee_id_descending':
        resources1 = society.resources.order_by('-ieee_id', '-name')
    
    elif sort == 'resource_type_ascending':
        resources1 = society.resources.order_by('resource_type', 'name')
    elif sort == 'resource_type_descending':
        resources1 = society.resources.order_by('-resource_type', '-name')
    
    elif sort == 'url_ascending':
        resources1 = society.resources.order_by('url', 'name')
    elif sort == 'url_descending':
        resources1 = society.resources.order_by('-url', '-name')
    
    elif sort == 'num_tags_ascending':
        resources1 = society.resources.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_tags',
        ])
    elif sort == 'num_tags_descending':
        resources1 = society.resources.extra(select={
            'num_tags': 'SELECT COUNT(ieeetags_resource_nodes.id) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_tags',
        ])
    
    elif sort == 'num_societies_ascending':
        resources1 = society.resources.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            'num_societies',
        ])
    elif sort == 'num_societies_descending':
        resources1 = society.resources.extra(select={
            'num_societies': 'SELECT COUNT(ieeetags_resource_societies.id) FROM ieeetags_resource_societies WHERE ieeetags_resource_societies.resource_id = ieeetags_resource.id',
        }, order_by=[
            '-num_societies',
        ])
    
    elif sort == '':
        # Default to name/ascending sort
        resources1 = society.resources.order_by('name')
    else:
        raise Exception('Unknown sort "%s"' % sort)
    
    # For each resource, get a list of society abbreviations in alphabetical order
    resources = []
    for resource in resources1:
        resource.society_abbreviations = [society1.abbreviation for society1 in resource.societies.order_by('abbreviation')]
        resources.append(resource)
    
    tags_tab_url = reverse('admin_manage_society', args=[society_id]) + '#tab-tags-tab'
    
    return render(request, 'site_admin/manage_society.html', {
        'sort': sort,
        'society': society,
        'form': form,
        'resources': resources,
        'tags_tab_url': tags_tab_url,
    })

@login_required
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
        
        print 'return_url:', return_url
        print 'society:', society
        print 'society.id:', society.id
        #print "reverse('admin_view_society', args=[society.id]):", reverse('admin_view_society', args=[society.id])
        url = reverse('admin_view_society', args=[society.id])
        print 'url:', url
        
        if return_url != '':
            return HttpResponseRedirect(return_url)
        else:
            #return HttpResponseRedirect(reverse('admin_view_society', args=[society.id]))
            return HttpResponseRedirect(url)

@login_required
def delete_society(request, society_id):
    Society.objects.get(id=society_id).delete()
    return HttpResponsePermanentRedirect(reverse('admin_societies'))

@login_required
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
def list_resources(request):
    resources = Resource.objects.all()
    return render(request, 'site_admin/list_resources.html', {
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
        })
        
        # Disable edit resource form fields for societies
        if not request.user.is_superuser:
            make_display_only(form.fields['societies'], is_multi_search=True)
            make_display_only(form.fields['ieee_id'])
        
    return render(request, 'site_admin/edit_resource.html', {
        'return_url': return_url,
        'resource': resource,
        'form': form,
    })

@login_required
def save_resource(request):
    if 'return_url' not in request.GET:
        raise Exception('query variable "return_url" not found')
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
        resource.description = form.cleaned_data['description']
        resource.url = form.cleaned_data['url']
        resource.nodes = form.cleaned_data['nodes']
        if form.cleaned_data['societies'] is not None:
            resource.societies = form.cleaned_data['societies']
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
    old_nodes = resource.nodes
    Resource.objects.get(id=resource_id).delete()
    _update_node_totals(old_nodes)
    return HttpResponsePermanentRedirect(reverse('admin_list_resources'))

@login_required
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

