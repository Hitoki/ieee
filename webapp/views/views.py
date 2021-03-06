from logging import debug as log
from random import randint
from datetime import datetime
import socket
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
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView
from xml.etree.ElementTree import fromstring
from django.conf import settings

from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, redirect, render
from django.template import RequestContext
import json
from django.contrib import auth
from django.contrib.auth.models import User
from django.contrib import messages

from core.decorators import optional_login_required as login_required
from webapp.forms import *
from webapp.models.node import Node
from webapp.models.society import Society
from webapp.models.types import ResourceType, Filter
from webapp.models.resource import Resource
from webapp.models.conference_application import TagKeyword, ConferenceApplication
from webapp.models.notification import ResourceAdditionNotificationRequest
from webapp.models.favorites import UserFavorites, UserExternalFavorites
from webapp.models.system import Cache

#from profiler import Profiler
from core import util
from core.widgets import make_display_only

from .xplore import _get_xplore_results
from .xplore import ajax_xplore_authors


TOOLTIP_MAX_CHARS = 120


# def render(request, template, dictionary=None):
#     """
#     Use this instead of 'render_to_response' to enable custom context
#     processors, which add things like MEDIA_URL to the page automatically.
#     """
#     return render_to_response(template, dictionary=dictionary,
#                               context_instance=RequestContext(request))

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
def textui(request, survey=False, account=False):
    """
    Shows the textui (aka. Tag Galaxy) UI.
    """
    node_id = request.GET.get('nodeId', None)
    sector_id = None
    cluster_id = None

    # If url ends with /survey set a session var so we can display an
    # additional banner.
    if survey:
        request.session['survey'] = True
        request.session.set_expiry(0)

    # NOTE: Disabled so we can land on the help page
    #if node_id is None:
    #    # Default to the first sector (instead of the help page)
    #    first_sector = Node.objects.getSectors()[0]
    #    node_id = first_sector.id

    if node_id is not None:
        # Node selected
        node = Node.objects.get(id=node_id)
        # Double check to make sure we didn't get a root or tag node
        if node.node_type.name == 'root':
            sector_id = Node.objects.getFirstSector().id
        elif node.node_type.name == 'tag':
            # TODO: a node has many sectors, for now just use the first one.
            sector_id = node.get_sectors()[0].id
        elif node.node_type.name == 'sector':
            sector_id = node_id
        elif node.node_type.name == 'tag_cluster':
            cluster_id = node_id
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
        'sectorId': sector_id,
        'clusterId': cluster_id,
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
        'ENABLE_JOYRIDE': enable_joyride,
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


def tag_landing(request, tag_id, node_slug=None):
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
    return print_resource(request, tag_id, 'all', node_slug,
                          node_type='tag',
                          template_name=template_name,
                          create_links=True, toc=True)


def clusters_list(request):
    """
    Displays a wikipedia-style "flat" view of the cluster.
    """
    return render(request, 'clusters_list.html', {
        'clusters': Node.objects.get_clusters(),
    })


def cluster_landing(request, cluster_id, node_slug=None):
    """
    Displays a wikipedia-style "flat" view of the cluster.
    No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    """
    return print_resource(request, cluster_id, 'all', node_slug,
                          node_type='tag_cluster',
                          template_name='cluster_landing.html',
                          create_links=True, toc=True)


XPLORE_SORT_PUBLICATION_YEAR = 'py'


def get_tv_xml_tree(tag_name):
    tv_url = "http://ieeetv.ieee.org/service/Signature" \
             "?url=http://ieeetv.ieee.org/service/VideosSearch?q=%s" % tag_name
    try:
        api_xml = fromstring(urllib2.urlopen(tv_url).read())
        dev_url = api_xml.find('url_dev').text  # get url from xml
        tv_xml = fromstring(urllib2.urlopen(dev_url).read())
        return tv_xml
    except (urllib2.URLError, socket.timeout):
        return None


def print_resource(request, tag_id, resource_type, node_slug='',
                   node_type=None, template_name='print_resource.html',
                   create_links=False, toc=False):
    """
    The print resource page.

    @param tag_id: The tag to print results for.
    @param resource_type: Which resource(s) to include.
    """
    tag = None
    try:
        tag = Node.objects.get(id=tag_id)
        if node_type in ["tag", "tag_cluster"] \
                and tag.node_type.name != node_type:
            # if wrong type of node - try to find one by slug
            raise ObjectDoesNotExist()
    except ObjectDoesNotExist:
        try:
            if node_type not in ["tag", "tag_cluster"]:
                # only tag and cluster urls has slugs in url
                # so there is no any info to process
                return HttpResponse("gone", status=410)  # gone
            if node_slug:  # if there is slug in the url
                # try to get name by slug (unslugify)
                name = node_slug.replace('-', ' ')
            else:
                if not tag:
                    # if there no slug and also no node with wrong node_type
                    return HttpResponse("gone", status=410)  # gone
                # get name from node with wrong node_type
                name = tag.name
            tag = Node.objects.get(name=name, node_type__name=node_type)
            # get url_name by node_type
            url_name = "cluster" if node_type == "tag_cluster" else node_type
            url_name = "%s_landing" % url_name
            if node_slug:
                args = [tag.id, node_slug]
            else:
                args = [tag.id]
            # permanent redirect (301)
            return redirect(url_name, *args, permanent=True)
        except ObjectDoesNotExist:
            return HttpResponse("gone", status=410)  # gone

    if request.user.is_authenticated():
        member = User.objects.get(id=request.user.id)
        email = request.user.email
        tag.is_favorite = UserFavorites.objects.filter(user=member).filter(topics=tag_id).exists()
        tag.enable_alerts = ResourceAdditionNotificationRequest.objects. \
            filter(email=email).filter(node_id=tag_id).exists()
    else:
        tag.is_favorite = False
        tag.enable_alerts = False

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
    xplore_edu_results = None
    total_edu_found = 0
    xplore_results = None
    total_xplore_found = 0
    xplore_authors = None
    total_xplore_authors_found = 0

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
        # Educational Courses:
        xplore_edu_results, xplore_edu_error, total_edu_found = \
            _get_xplore_results(tag.name, False, ctype='Educational Courses')
        # Videos:
        tv_xml = get_tv_xml_tree(tag.name)
        tv_html = ""
        if tv_xml is not None:
            results = tv_xml.findall('search-item')
            tv_count = len(results)
            for result in results:
                thumb = result.find('images').find('thumbnail').text
                title = result.find('title').text
                url = result.find('web-page').text
                tv_html += '<img src="%s" height="60" width="105"/>' \
                           '<a href="%s" target="_blank">%s ' \
                           '<span class="popup newWinIcon"></span>' \
                           '</a><br>\n' % (thumb, url, title)
        # E-Books:
        ebooks = \
            Resource.objects.getForNode(tag, resourceType=ResourceType.EBOOK)
    if resource_type == 'xplore' or resource_type == 'all':
        xplore_results, xplore_error, total_xplore_found = \
            _get_xplore_results(tag.name, False)

    if resource_type == 'authors' or resource_type == 'all':
        xplore_authors, xplore_error, total_xplore_authors_found = ajax_xplore_authors(tag_id)

    page_date = datetime.now()

    related_items_count = \
        sectors.count() + related_tags.count() + societies.count() + \
        conf_count + periodicals.count() + standards.count() +\
        (total_edu_found
         if isinstance(total_edu_found, int)
         else 0
        ) +\
        (total_xplore_found
         if isinstance(total_xplore_found, int)
         else 0
        ) +\
        (total_xplore_authors_found
         if isinstance(total_xplore_authors_found, int)
         else 0
        )

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
        profile = request.user.profile
        profile.last_logout_time = datetime.now()
        profile.save()
    auth.logout(request)

    messages.success(request, "You have been signed out.")

    referer = request.META.get('HTTP_REFERER', None)
    if referer is None:
        pass
        # do something here
    try:
        redirect_to = urlsplit(referer, 'http', False)[2]
    except IndexError:
        pass
    # do another thing here
    return HttpResponseRedirect(redirect_to)

    #if settings.USE_SITEMINDER_LOGIN:
    #host = request.META['HTTP_HOST']
    #if host.count('.') > 1:
    #    host = host[host.find('.'):]
    #response.delete_cookie("SMSESSION", domain=host)
    #return response


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
    if offset:
        jobs_url = "%s?%s&rows=25&page=%s&format=json" % \
                   (settings.JOBS_URL,
                    urllib.urlencode({"kwsMustContainPhrase": tag.name}),
                    offset)
    else:
        jobs_url = "%s?%s&rows=25&format=json" % \
                   (settings.JOBS_URL,
                    urllib.urlencode({"kwsMustContainPhrase": tag.name}))
    try:
        content = urllib2.urlopen(jobs_url).read()
    except (urllib2.URLError, socket.timeout):
        jobs_html = []
        jobs_count = "N/A"
        return jobs_html, jobs_count, jobs_url
    jobs_json = json.loads(content)
    jobs_count = jobs_json.get('Total')
    jobs = jobs_json.get('Jobs')
    user_favorites = \
        UserExternalFavorites.objects.get_external_ids('job', user)
    jobs_html = '<ul>'
    for job in jobs:
        job_id = job['Id']
        job['Star'] = ''
        if user and user.is_authenticated():
            if job_id in user_favorites:
                job['StarClass'] = 'icon-star-whole enabled'
                job['TitleText'] = 'Remove job from Your Favorites'
            else:
                job['StarClass'] = 'icon-star'
                job['TitleText'] = 'Add job to Your Favorites'
            job['Star'] = \
                '<span class="%(StarClass)s favorite-job icomoon-icon"'\
                ' data-nodeid="%(Id)s" data-rtype="job"' \
                ' title="%(TitleText)s"></span>' % job
        if user and not user.is_authenticated():
            job['Star'] = \
                '<span class="deferRegister icon-star icomoon-icon" title="Join IEEE Technology Navigator<br/>to add topic to favorites."></span>'
        jobs_html += '<li><span class="newWinTrigger">' \
                     '<a href="%(Url)s" target="_blank" class="featured">'\
                     '%(JobTitle)s</a><span class="popup newWinIcon"></span>' \
                     '</span>%(Star)s<p>%(Company)s</p>\n' % job
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
    user_id = request.user.id
    User.objects.filter(id=user_id).delete()
    messages.add_message(request, messages.SUCCESS,
                         'Your account has been deleted.')
    return HttpResponseRedirect(reverse('textui'))


@login_required
def clear_cache(request, pk=None):
    if pk:
        Cache.objects.filter(pk=pk).delete()
        return HttpResponse('cache %d cleared' % pk)
    else:
        Cache.objects.all().delete()
        return HttpResponse('cache cleared')


@login_required
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


class LoginRedirectView(TemplateView):
    template_name = "socialaccount/login_redirect.html"
