from logging import debug as log
from random import randint
from datetime import datetime
from urlparse import urlsplit
import re
import sys
import traceback
import urllib
import urllib2
import hotshot
import os
import time
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
import settings


from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils import simplejson as json
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages

from decorators import optional_login_required as login_required
from ieeetags.forms import *
from models.node import Node
from models.society import Society
from models.types import ResourceType, Filter
from models.resource import Resource
from models.conference_application import TagKeyword, ConferenceApplication
from models.favorites import UserFavorites, UserExternalFavorites

#from profiler import Profiler
import util
from widgets import make_display_only

from .xplore import _get_xplore_results
from .xplore import ajax_xplore_authors


TOOLTIP_MAX_CHARS = 120


def render(request, template, dictionary=None):
    """
    Use this instead of 'render_to_response' to enable custom context
    processors, which add things like MEDIA_URL to the page automatically.
    """
    return render_to_response(template, dictionary=dictionary,
                              context_instance=RequestContext(request))

# ----------------------------------------------------------------------------


def error_view(request):
    """
    Custom error view for production servers.  Sends an email to admins for
    every error with a traceback.

    Only active when settings.DEBUG == True.
    """

    # Get the latest exception from Python system service 
    (type, value, traceback1) = sys.exc_info()
    traceback1 = '.'.join(traceback.format_exception(type, value, traceback1))

    # Send email to admins
    subject = 'Error in ieeetags: %s, %s' % (str(type), value)
    message = traceback1
    mail_admins(subject, message, True)

    title = None
    message = None

    if type is util.EndUserException:
        title, message = value

    return render(request, '500.html', {
        'title': title,
        'message': message,
    })


def site_disabled(request):
    """
    Displays "site disabled" message when the entire site is disabled
    (settings.DISABLE_SITE == True).
    """
    return render(request, 'site_disabled.html', {})


@login_required
def index(request):
    if request.META['HTTP_HOST'].startswith('m.'):
        return render_to_response('index_mobile.html', {},
                                  context_instance=RequestContext(request))
    # Redirects user to textui page.
    return HttpResponseRedirect(reverse('textui'))


@login_required
def roamer(request):
    """
    Shows the Asterisq Constellation Roamer flash UI.
    """
    node_id = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId': node_id,
        'sectors': sectors,
        'filters': filters,
    })


@login_required
def textui(request, survey=False):
    """
    Shows the textui (aka. Tag Galaxy) UI.
    """
    nodeId = request.GET.get('nodeId', None)
    sectorId = None
    clusterId = None

    # If url ends with /survey set a session var so we can display an
    # additional banner.
    if survey:
        request.session['survey'] = True
        request.session.set_expiry(0)

    # NOTE: Disabled so we can land on the help page
    #if nodeId is None:
    #    # Default to the first sector (instead of the help page)
    #    first_sector = Node.objects.getSectors()[0]
    #    nodeId = first_sector.id

    if nodeId is not None:
        # Node selected
        node = Node.objects.get(id=nodeId)
        # Double check to make sure we didn't get a root or tag node
        if node.node_type.name == 'root':
            sectorId = Node.objects.getFirstSector().id
        elif node.node_type.name == 'tag':
            # TODO: a node has many sectors, for now just use the first one.
            sectorId = node.get_sectors()[0].id
        elif node.node_type.name == 'sector':
            sectorId = nodeId
        elif node.node_type.name == 'tag_cluster':
            clusterId = nodeId
        else:
            raise Exception('Unknown node_type "%s"' % node.node_type.name)

    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    societies = Society.objects.all()

    # NOTE: Hide TAB society from the nav.
    societies = societies.exclude(abbreviation__in=['tab', 'ieee-usa'])

    template = 'textui_new.html'
    NEWUI = True
    newui_search_button = False

    enable_joyride = settings.ENABLE_JOYRIDE

    return render(request, template, {
        'sectorId': sectorId,
        'clusterId': clusterId,
        'sectors': sectors,
        'filters': filters,
        'societies': societies,
        'ENABLE_SHOW_CLUSTERS_CHECKBOX':
            settings.ENABLE_SHOW_CLUSTERS_CHECKBOX,
        'ENABLE_SHOW_TERMS_CHECKBOX': settings.ENABLE_SHOW_TERMS_CHECKBOX,
        'ENABLE_SEARCH_BUTTON': settings.ENABLE_SEARCH_BUTTON,
        'SEARCH_KEY_DELAY': settings.SEARCH_KEY_DELAY,
        'NEWUI': NEWUI,
        'ENABLE_SEARCH_BUTTON': newui_search_button,
        'ENABLE_JOYRIDE': enable_joyride
    })


@login_required
def textui_home(request):
    """
    Shows textui "home" AJAX page.
    """
    return render(request, 'textui_home.html')


@login_required
def textui_help(request):
    """
    Shows textui "help" AJAX page.
    """
    return render(request, 'textui_help.html')


@login_required
def feedback(request):
    """
    User feedback page.  When submitted, sends an email to all admins.
    """
    if request.method == 'GET':
        if request.user.is_authenticated and not request.user.is_anonymous:
            form = FeedbackForm(
                initial={
                    'name': '%s %s' % (request.user.first_name,
                                       request.user.last_name),
                    'email': request.user.email,
                }
            )

            make_display_only(form.fields['name'])
            make_display_only(form.fields['email'])

        else:
            form = FeedbackForm()
        return render(request, 'feedback.html', {
            'form': form,
        })
    else:
        form = FeedbackForm(request.POST)
        if form.is_valid():

            # Send email
            subject = 'IEEE Comments from %s' % form.cleaned_data['email']
            message = 'Sent on %s:\n%s\n\n' % \
                      (time.strftime('%Y-%m-%d %H:%M:%S'),
                       form.cleaned_data['comments'])
            send_from = settings.DEFAULT_FROM_EMAIL
            send_to = settings.ADMIN_EMAILS
            try:
                send_mail(subject, message, send_from, send_to)
            except Exception, e:
                email_error = True
            else:
                email_error = False

            return render(request, 'feedback_confirmation.html', {
                'email_error': email_error,
            })
        else:
            return render(request, 'feedback.html', {
                'form': form,
            })


def browser_warning(request):
    """
    Shows the AJAX browser compatability warning page.
    Allows the user to click through if they still want to browse the site.
    """
    return render(request, 'browser_warning.html')


def tester_message(request):
    """
    Returns the HTML content for the tester message.
    """
    return render(request, 'tester_message.html')


def tester_survey(request):
    """
    Returns the HTML content for the tester survey.
    """
    return render(request, 'tester_survey.html')


try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except:
    PROFILE_LOG_BASE = "/tmp"


def profile(log_file):
    """
    Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into the
    file name, such that 'my_view.prof' become 'my_view-20100211T170321.prof', 
    where the time stamp is in UTC. This makes it easy to run and compare 
    multiple trials.     
    """
    if not os.path.isabs(log_file):
        log_file = os.path.join(PROFILE_LOG_BASE, log_file)

    def _outer(f):
        def _inner(*args, **kwargs):
            # Add a timestamp to the profile output when the callable
            # is actually called.
            (base, ext) = os.path.splitext(log_file)
            base = base + "-" + time.strftime("%Y%m%dT%H%M%S", time.gmtime())
            final_log_file = base + ext

            prof = hotshot.Profile(final_log_file)
            try:
                ret = prof.runcall(f, *args, **kwargs)
            finally:
                prof.close()
            return ret

        return _inner

    return _outer


def tags_list(request):
    """
    Displays a list of links to the tag "wikipedia-style" pages
    (see views.tag_landing)
    Mostly useful for spider link discovery and SEO.
    """
    is_staff = request.user.is_staff
    return render_to_response('tags_list.html',
                              {"tags": Node.objects.get_tags(),
                               "show_id": is_staff,
                               "show_resource_count": is_staff,
                               "show_checkbox": is_staff},
                              context_instance=RequestContext(request))


def tags_all(request):
    """
    Displays a list of "high_potency" links to the tag "wikipedia-style"
    pages (see views.tag_landing)
    """

    nodes = Node.objects.filter(high_potency=True)

    return render_to_response('tags_all.html', {"tags": nodes},
                              context_instance=RequestContext(request))


def tags_starts(request, starts_with):
    nodes = Node.objects.filter(high_potency=False,
                                name__iregex='^' + starts_with)
    return render_to_response('tags_list.html', {"tags": nodes},
                              context_instance=RequestContext(request))


def tag_landing(request, tag_id):
    """
    Displays a wikipedia-style flat view of the tag. No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    """
    # TODO move logic to decorator
    is_mobile = (
        re.match(settings.MOBILE_URL_PREFIX, request.META['HTTP_HOST']) and
        not ('nomobile' in request.GET and request.GET['nomobile'] == "1")
    )
    if is_mobile:
        template_name = 'tag_landing_mobile.html'
    else:
        template_name = 'tag_landing.html'
    return print_resource(request, tag_id, 'all', template_name=template_name,
                          create_links=True, toc=True)


def clusters_list(request):
    """
    Displays a wikipedia-style "flat" view of the cluster.
    """
    return render(request, 'clusters_list.html', {
        'clusters': Node.objects.get_clusters(),
    })


def cluster_landing(request, cluster_id):
    """
    Displays a wikipedia-style "flat" view of the cluster.
    No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    """
    return print_resource(request, cluster_id, 'all',
                          template_name='cluster_landing.html',
                          create_links=True, toc=True)


XPLORE_SORT_PUBLICATION_YEAR = 'py'


def print_resource(request, tag_id, resource_type,
                   template_name='print_resource.html', create_links=False,
                   toc=False):
    """
    The print resource page.

    @param tag_id: The tag to print results for.
    @param resource_type: Which resource(s) to include.
    """
    tag = Node.objects.get(id=tag_id)

    sectors = Node.objects.none()
    related_tags = Node.objects.none()
    societies = Society.objects.none()
    conferences = Node.objects.none()
    patents = resource_type == 'patents' or resource_type == 'all'
    periodicals = Node.objects.none()
    standards = Node.objects.none()
    ebooks = Node.objects.none()
    jobs_html = ''
    tv_html = ''
    conf_count = 0
    totalfound = 0
    xplore_edu_results = None
    totaledufound = 0
    xplore_results = None
    xplore_authors = None

    resource_types = ['all', 'sectors', 'related_tags', 'societies',
                      'conferences', 'periodicals', 'standards', 'xplore_edu',
                      'xplore', 'jobs', 'patents', 'overview', 'authors']
    if resource_type not in resource_types:
        raise Exception('Unknown resource_type "%s"' % resource_type)

    if resource_type == 'sectors' or resource_type == 'all':
        # TODO: Need to filter clusters out here?
        sectors = tag.parents.all()
    if resource_type == 'related_tags' or resource_type == 'all':
        related_tags = tag.related_tags.all()
    if resource_type == 'societies' or resource_type == 'all':
        societies = tag.societies.all()
    if resource_type == 'conferences' or resource_type == 'all':
        conferences = \
            Resource.objects.getForNode(tag,
                                        resourceType=ResourceType.CONFERENCE)
        if template_name in ('tag_landing.html', 'tag_landing_mobile.html'):

            for conference in conferences:
                check_url = len(conference.url.strip()) and \
                            not re.compile('^https?://').match(conference.url)
                if check_url:
                    conference.url = 'http://' + conference.url

            # Sort the conferences by year latest to earliest.
            conferences = list(sorted(conferences,
                                      key=lambda resource: resource.year,
                                      reverse=True))
            conferences = util.group_conferences_by_series(conferences)
            conf_count = len(conferences)
        else:
            conf_count = conferences.count()
    if resource_type == 'periodicals' or resource_type == 'all':
        periodicals = \
            Resource.objects.getForNode(tag,
                                        resourceType=ResourceType.PERIODICAL)
    if resource_type == 'standards' or resource_type == 'all':
        standards = \
            Resource.objects.getForNode(tag,
                                        resourceType=ResourceType.STANDARD)
    if resource_type == 'xplore_edu' or resource_type == 'all':
        xplore_edu_results, xplore_edu_error, totalfound = \
            _get_xplore_results(tag.name, False, ctype='Educational Courses')

        # jobs_results, jobs_error, num_results = \
        #     _get_xplore_results(name, show_all=show_all, offset=offset,
        #                         sort=sort, sort_desc=sort_desc, ctype=ctype)
        tvUrl = "http://ieeetv.ieee.org/service/Signature?url=" \
                "http://ieeetv.ieee.org/service/VideosSearch?q=%s" % tag.name
        file2 = urllib2.urlopen(tvUrl).read()

        # get url from xml that is returned
        from xml.etree.ElementTree import fromstring

        apixml = fromstring(file2)
        dev_url = apixml.find('url_dev').text

        tv_xml = fromstring(urllib2.urlopen(dev_url).read())

        results = tv_xml.findall('search-item')
        tvCount = len(results)

        tv_html = ""
        for result in results:
            thumb = result.find('images').find('thumbnail').text
            title = result.find('title').text
            url = result.find('web-page').text
            tv_html += '<img src="%s" height="60" width="105"/>' \
                      '<a href="%s" target="_blank">%s ' \
                      '<span class="popup newWinIcon"></span>' \
                      '</a><br>\n' % (thumb, url, title)

        ebooks = Resource.objects.getForNode(tag,
                                             resourceType=ResourceType.EBOOK)
    if resource_type == 'xplore' or resource_type == 'all':
        xplore_results, xplore_error, totalfound = \
            _get_xplore_results(tag.name, False)

    if resource_type == 'authors' or resource_type == 'all':
        xplore_authors, xplore_error, totalfound = ajax_xplore_authors(tag_id)

    page_date = datetime.now()

    related_items_count = sectors.count() + related_tags.count() + \
                          societies.count() + conf_count + \
                          periodicals.count() + standards.count() + \
                          totaledufound + totalfound

    if resource_type == 'jobs' or resource_type == 'all':
        jobs_html, jobs_count, jobs_url = get_jobs_info(tag)

    try:
        xplore_article = \
            _get_xplore_results(tag.name, show_all=False, offset=0,
                                sort=XPLORE_SORT_PUBLICATION_YEAR,
                                sort_desc=True)[0][0]
    except IndexError:
        xplore_article = None

    if toc is True:
        overview = False
    elif resource_type == 'overview':
        overview = True
    elif resource_type == 'all':
        overview = True
    else:
        overview = False

    if xplore_edu_results:
        show_edu = True
    elif tv_html:
        show_edu = True
    elif ebooks:
        show_edu = True
    else:
        show_edu = False

    return render(request, template_name, {
        'page_date': page_date,
        'tag': tag,
        'sectors': sectors,
        'related_tags': related_tags,
        'societies': societies,
        'conferences': conferences,
        'patents': patents,
        'periodicals': periodicals,
        'standards': standards,
        'xplore_edu_results': xplore_edu_results,
        'xplore_results': xplore_results,
        'authors': xplore_authors,
        'toc': toc,
        'create_links': create_links,
        'related_items_count': related_items_count,
        'jobsHtml': jobs_html,
        #'tvHtml': tvHtml,
        'close_conference': tag._get_closest_conference(),
        'definition': tag._get_definition_link(),
        'xplore_article': xplore_article,
        'tvHtml': tv_html,
        'ebooks': ebooks,
        'overview': overview,
        'show_edu': show_edu
    })

def log_out(request):
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        profile.last_logout_time = datetime.now()
        profile.save()
    auth.logout(request)
    
    messages.success(request, "You have been signed out.")
    response = HttpResponseRedirect(reverse('index'))
    
    #if settings.USE_SITEMINDER_LOGIN:
    host = request.META['HTTP_HOST']
    if host.count('.') > 1:
        host = host[host.find('.'):]
    response.delete_cookie("SMSESSION", domain=host)
    return response

def debug_error(request):
    """
    DEBUG: Causes an error, to test the error handling.
    """
    test = 0 / 0


@login_required
def debug_send_email(request):
    """
    DEBUG: Tests sending an email.
    """
    assert request.user.is_superuser, 'Page disabled for non superusers.'

    log('sending email to "%s"' % request.user.email)
    subject = 'debug_send_email() to "%s"' % request.user.email
    message = 'debug_send_email() to "%s"' % request.user.email
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL,
              [request.user.email], fail_silently=False)
    log('email sent.')
    return HttpResponse('Email sent to "%s"' % request.user.email)


def test_error(request):
    """
    DEBUG: Tests causing an error.
    """
    assert settings.DEBUG
    # Divide by zero error
    1 / 0
    return render(request, 'test_error.html')


def test_lightbox_error(request):
    """
    DEBUG: Tests a lightbox error.
    """
    assert settings.DEBUG
    return render(request, 'test_lightbox_error.html')


def test_browsers(request):
    """
    DEBUG: Tests a browsers error.
    """
    assert settings.DEBUG
    return render(request, 'test_browsers.html')


def get_jobs_info(tag, offset=None, user=None):
    jobs_html = ''
    if offset:
        jobs_url = "%s?%s&rows=25&page=%s&format=json" % \
                  (settings.JOBS_URL,
                   urllib.urlencode({"kwsMustContainPhrase": tag.name}),
                   offset)
    else:
        jobs_url = "%s?%s&rows=25&format=json" % \
                  (settings.JOBS_URL,
                   urllib.urlencode({"kwsMustContainPhrase": tag.name}))
    file1 = urllib2.urlopen(jobs_url).read()
    jobs_json = json.loads(file1)
    jobs_count = jobs_json.get('Total')
    jobs = jobs_json.get('Jobs')
    user_favorites = UserExternalFavorites.objects.filter(user=user).\
        filter(external_resource_type='job').\
        values_list('external_id', flat=True)
    jobs_html = '<ul>'
    for job in jobs:
        job_id = job['Id']
        if job_id in user_favorites:
            job['StarClass'] = 'icon-star-whole enabled'
        else:
            job['StarClass'] = 'icon-star'
        jobs_html += '<li><a href="%(Url)s" target="_blank" class="featured">' \
                     '%(JobTitle)s<span class="popup newWinIcon"></span></a>' \
                     '<span class="%(StarClass)s favorite-job icomoon-icon" ' \
                     'data-nodeid="%(Id)s"></span>' \
                     '<p>%(Company)s</p>\n' % job
    jobs_html += '</ul>'
    return jobs_html, jobs_count, jobs_url


def debug_conf_app_create(request):
    conf_app_name = "ConferenceApplication_%d" % randint(1, 100)
    conf_app = ConferenceApplication.objects.create(name=conf_app_name)
    for i in range(randint(2, 4)):
        keyword_name = "keyword_%d" % randint(1, 10)
        keyword, created = TagKeyword.objects.get_or_create(name=keyword_name)
        conf_app.keywords.add(keyword)
    just_for_example = ["Acoustics", "Controls", "Design"]
    node = Node.objects.get(name=just_for_example[randint(0, 2)])
    keyword, created = TagKeyword.objects.get_or_create(name=node.name,
                                                        tag=node)
    conf_app.keywords.add(keyword)
    return redirect('conference_applications')


class ConferenceApplicationListView(ListView):
    template_name = "conference_application/list.html"
    model = ConferenceApplication
    context_object_name = "items"


class ConferenceApplicationCreateView(CreateView):
    template_name = "conference_application/create.html"
    form_class = ConferenceApplicationForm

    def get_success_url(self):
        return reverse('conference_applications')


def debug_conf_apps_by_keyword(request, keyword_name):
    keyword = TagKeyword.objects.get(name=keyword_name)
    items = keyword.conference_applications.all()
    return render(request, "conference_application/list.html",
                  dict(keyword_name=keyword_name, items=items))
    # return HttpResponseRedirect(reverse('index'))


def delete_user(request):
    user_id=request.user.id
    User.objects.filter(id=user_id).delete()
    messages.add_message(request, messages.SUCCESS, 'Your account has been deleted.')
    return HttpResponseRedirect(reverse('textui'))


def allauth_init(request):
    site = Site.objects.filter(id=1)
    site.name = 'newdev.systemicist.com'
    site.domain = 'newdev.systemicist.com'
    SocialApp.objects.all().delete()
    for provider, data in settings.SOCIALACCOUNT_KEYS.items():
        app = SocialApp.objects.create(
            provider=provider, name=provider, key=provider,
            client_id=data['client_id'], secret=data['secret'])
        app.sites.add(settings.SITE_ID)
    return HttpResponse('allauth_init - ok')
