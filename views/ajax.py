import datetime
from logging import debug as log
import math
import re
import string
import traceback
import urllib
import urllib2
import xml.dom.minidom
import hotshot
import os
import time
from xml.etree.ElementTree import fromstring

from django.core import serializers
from django.core.mail import mail_admins, send_mail
from django.core.urlresolvers import reverse
from django.db.models import Count, Q
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson as json
from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response, get_object_or_404

from django.template import RequestContext
from django.template.loader import render_to_string
from django.contrib.auth.models import User
import sys

from decorators import optional_login_required as login_required
from ieeetags.forms import *

#from profiler import Profiler
from models.logs import ProfileLog
from models.node import Node
from models.node_extra import get_node_extra_info
from models.notification import ResourceAdditionNotificationRequest
from models.profile import Profile
from models.resource import Resource
from models.society import Society
from models.system import Cache
from models.types import NodeType, ResourceType, Filter
from models.utils import single_row
from models.favorites import UserFavorites
import settings
import util
from BeautifulSoup import BeautifulSoup

from .views import render, get_jobs_info
from widgets import make_display_only
from .xplore import _get_xplore_results, ajax_xplore_authors


TOOLTIP_MAX_CHARS = 120


def render(request, template, dictionary=None):
    """Use this instead of 'render_to_response' to enable
    custom context processors, which add things like MEDIA_URL to the page
    automatically."""
    return render_to_response(template, dictionary=dictionary,
                              context_instance=RequestContext(request))

# ----------------------------------------------------------------------------


def error_view(request):
    '''
    Custom error view for production servers.
    Sends an email to admins for every error with a traceback.
    
    Only active when settings.DEBUG == True.
    '''

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
    '''Displays "site disabled" message when the entire site is disabled
    (settings.DISABLE_SITE == True).'''
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
    '''Shows the Asterisq Constellation Roamer flash UI.'''
    nodeId = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId': nodeId,
        'sectors': sectors,
        'filters': filters,
    })


@login_required
def textui(request, survey=False):
    '''Shows the textui (aka. Tag Galaxy) UI.'''
    nodeId = request.GET.get('nodeId', None)
    sectorId = None
    clusterId = None

    # If url ends with /survey set a session var so we can display
    # an additional banner.
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
    newui_search_button = False

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
        'ENABLE_SEARCH_BUTTON': newui_search_button
    })


@login_required
def textui_home(request):
    '''Shows textui "home" AJAX page.'''
    return render(request, 'textui_home.html')


@login_required
def textui_help(request):
    '''Shows textui "help" AJAX page.'''
    return render(request, 'textui_help.html')


@login_required
def feedback(request):
    '''User feedback page.  When submitted, sends an email to all admins.'''
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
    '''Shows the AJAX browser compatability warning page.
    Allows the user to click through if they still want to browse the site.'''
    return render(request, 'browser_warning.html')


try:
    PROFILE_LOG_BASE = settings.PROFILE_LOG_BASE
except:
    PROFILE_LOG_BASE = "/tmp"


def profile(log_file):
    """Profile some callable.

    This decorator uses the hotshot profiler to profile some callable (like
    a view function or method) and dumps the profile data somewhere sensible
    for later processing and examination.

    It takes one argument, the profile log name. If it's a relative path, it
    places it under the PROFILE_LOG_BASE. It also inserts a time stamp into
    the file name, such that 'my_view.prof' become
    'my_view-20100211T170321.prof', where the time stamp is in UTC.
    This makes it easy to run and compare multiple trials.
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


@login_required
#@profile("ajax_tag.prof")
def ajax_tag_content(request, tag_id, ui=None, tab='overview'):
    context = {}
    tab_template = None

    try:
        if request.GET['load_framework'] == 'True':
            load_framework = True
    except:
        load_framework = None

    'The AJAX resource results popup.'
    if ui is None:
        ui = 'textui'
    assert ui in ['roamer', 'textui'], 'Unrecognized ui "%s"' % ui
    context['tab'] = tab
    context['ui'] = ui

    tag = Node.objects.get(id=tag_id)
    context['tag'] = tag

    counts = 0
    tvCount = "0"

    #sectors1 = tag.get_sectors()
    #counts += sectors1.count()

    clusters1 = tag.get_parent_clusters()

    # Build a list of sectors and clusters, grouped by sector
    #parent_nodes = []
    #for sector in sectors1:
    #    clusters = []
    #    for cluster in clusters1:
    #        if sector in cluster.parents.all():
    #            clusters.append(cluster)
    #    
    #    parent_nodes.append({
    #        'sector': sector,
    #        'clusters': clusters,
    #    })
    #context['parent_nodes'] = parent_nodes

    #num_resources = Resource.objects.getForNode(tag).count()
    #context['num_resources'] = num_resources

    # experts = Resource.objects.getForNode(tag,
    #                                       resourceType=ResourceType.EXPERT)
    #counts += experts.count()
    #context['experts'] = experts

    # Grab standards with is_machine_generated field.
    if tab == 'standard':
        standards_resource_nodes = \
            tag.resource_nodes.filter(
                resource__resource_type__name=ResourceType.STANDARD)
        standards = []
        for standards_resource_node in standards_resource_nodes:
            standard = standards_resource_node.resource
            standard.is_machine_generated = \
                standards_resource_node.is_machine_generated
            standards.append(standard)

        counts += len(standards)
        context['standards'] = standards
        tab_template = 'ajax_standard_tab.inc.html'
        context['loaded'] = True

    if tab == 'periodical':
        # Grab periodicals with is_machine_generated field.
        periodicals_resource_nodes = \
            tag.resource_nodes.filter(
                resource__resource_type__name=ResourceType.PERIODICAL)
        periodicals = []
        for periodicals_resource_node in periodicals_resource_nodes:
            periodical = periodicals_resource_node.resource
            periodical.is_machine_generated = \
                periodicals_resource_node.is_machine_generated
            periodicals.append(periodical)

        counts += len(periodicals)
        context['periodicals'] = periodicals
        tab_template = 'ajax_periodical_tab.inc.html'
        context['loaded'] = True

    if tab == 'conference':
        # Sort the conferences by year latest to earliest.
        conferences_resource_nodes = \
            tag.resource_nodes.filter(
                resource__resource_type__name=ResourceType.CONFERENCE)
        conferences = []
        for conferences_resource_node in conferences_resource_nodes:
            conference = conferences_resource_node.resource
            conference.is_machine_generated = \
                conferences_resource_node.is_machine_generated
            if not re.compile('^https?://').match(conference.url):
                conference.url = 'http://' + conference.url
            conferences.append(conference)

        conferences = list(sorted(conferences,
                                  key=lambda resource: resource.year,
                                  reverse=True))
        conferences = util.group_conferences_by_series(conferences)
        counts += len(conferences)
        context['conferences'] = conferences
        tab_template = 'ajax_conferences_tab.inc.html'
        context['loaded'] = True

    if tab == 'society':
        societies = tag.societies.all()
        # Hide the TAB society.
        societies = societies.exclude(abbreviation='tab')
        counts += societies.count()
        context['societies'] = societies
        tab_template = 'ajax_organizations_tab.inc.html'
        context['loaded'] = True

    if tab == 'education':
        ebooks_resource_nodes = \
            tag.resource_nodes.filter(
                resource__resource_type__name=ResourceType.EBOOK)
        ebooks = []
        for ebooks_resource_node in ebooks_resource_nodes:
            ebook = ebooks_resource_node.resource
            ebook.is_machine_generated = \
                ebooks_resource_node.is_machine_generated
            ebooks.append(ebook)

        counts += len(ebooks)
        context['ebooks'] = ebooks
        tab_template = 'ajax_ebook_results.inc.html'
        context['loaded'] = True

    if tab == 'tv':
        #http://ieeetv.ieee.org/service/Signature
        #http://ieeetv.ieee.org/service/Signature?url=
        # http://ieeetv.ieee.org/service/VideosSearch?q=ieee
        tvUrl = "http://ieeetv.ieee.org/service/Signature?url=" \
                "http://ieeetv.ieee.org/service/VideosSearch?q=%s" % \
                urllib.urlencode({"kwsMustContain": tag.name})
        file2 = urllib2.urlopen(tvUrl).read()
        tvJson = json.loads(file1)
        tvCount = tvJson.get('Total')
        tvUrl = tvUrl.replace('&format=json', '')
        tab_template = 'ajax_tv_tab.inc.html'
        context['tvCount'] = tvCount
        context['tvUrl'] = tvUrl
        context['loaded'] = True

    if tab == 'overview':
        #try:
        #    xplore_article = ajax_recent_xplore(tag.name)
        #    xplore_article = _get_xplore_results(
        #        tag.name, show_all=False, offset=0,
        #        sort=XPLORE_SORT_PUBLICATION_YEAR, sort_desc=True,
        #        recent=True)[0][0]
        #except IndexError:
        #    xplore_article = None

        #context['xplore_article'] = xplore_article
        context['close_conference'] = tag._get_closest_conference()
        context['definition'] = tag._get_definition_link()

        member = request.user
        related_tags = tag.related_tags.all()
        for related_tag in related_tags:
            if request.user.is_authenticated():
                member = User.objects.get(id=request.user.id)
                is_favorite = UserFavorites.objects.filter(user=member).filter(favorites=related_tag).exists()
            else:
                is_favorite = False
            related_tag.is_favorite = is_favorite

        context['related_tags'] = related_tags

        tab_template = 'ajax_over_tab.inc.html'

    file1 = None
    # removied sectors from count
    num_related_items = counts + clusters1.count()
    # tag.related_tags.count()

    #context['num_related_items'] = num_related_items

    # Determines if current tag is in user's list of favorites
    if request.user.is_authenticated():
        member = User.objects.get(id=request.user.id)
        is_favorite = UserFavorites.objects.filter(user=member).filter(favorites=tag).exists()
    else:
        is_favorite = False

    context['is_favorite'] = is_favorite

    # Determines if user is subscribed to tag alerts
    if request.user.is_authenticated():
        email = request.user.email
        enable_alerts = ResourceAdditionNotificationRequest.objects.filter(email=email).filter(node_id=tag.id).exists()
    else:
        enable_alerts = False
    context['enable_alerts'] = enable_alerts

    try:
        show_tv = settings.SHOW_TV_TAB
    except AttributeError:
        show_tv = False

    if show_tv:
        context['show_tv'] = True
    else:
        context['show_tv'] = False

    if load_framework:
        # Show the normal tag content popup.
        return render(request, 'ajax_tag_content.html', context)
    else:
        # return the specific tab's template
        return render(request, tab_template, context)


#@login_required
#def ajax_term_content(request, term_id, ui=None):
#    'The AJAX resource results popup for taxonomy terms.'
#    if ui is None:
#        ui = 'textui'
#    assert ui in ['roamer', 'textui'], 'Unrecognized ui "%s"' % ui
#    
#    term = TaxonomyTerm.objects.get(id=term_id)
#    num_related_items = term.related_nodes.count()
#    
#    return render(request, 'ajax_term_content.html', {
#        'term':term,
#        'num_related_items': num_related_items,
#        'ui': ui,
#    })


@csrf_exempt
def ajax_jobs_results(request):
    '''
    Shows the list of IEEE xplore articles for the given tag.
    @param tag_id: POST var, specifyies the tag.
    @param show_all: POST var, ("true" or "false"): if true, return all rows.
    @param offset: POST var, int: the row to start at.
    @param token: POST var, the ajax token to pass through.
    @return: HTML output of results.
    '''
    tag_id = request.POST.get('tag_id')

    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        name = tag.name
    else:
        assert False, 'Must specify tag_id.'

    show_all = (request.POST['show_all'] == 'true')
    offset = int(request.POST.get('offset', 0))
    token = request.POST['token']

    # jobs_results, jobs_error, num_results = _get_xplore_results(
    #     name, show_all=show_all, offset=offset, sort=sort,
    #     sort_desc=sort_desc, ctype=ctype)

    jobsHtml, jobsCount, jobsUrl = get_jobs_info(tag, offset)

    # DEBUG:
    #xplore_error = 'BAD ERROR.'

    data = {
        'num_results': jobsCount,
        'html': jobsHtml,
        'search_term': name,
        'token': token,
        'job_url': jobsUrl.replace('&format=json', ''),
    }

    return HttpResponse(json.dumps(data), 'application/javascript')


@csrf_exempt
def ajax_tv_results(request):
    '''
    Shows the list of IEEE xplore articles for the given tag.
    @param tag_id: POST var, specifyies the tag.
    @param show_all: POST var, ("true" or "false"): if true, return all rows.
    @param offset: POST var, int: the row to start at.
    @param token: POST var, the ajax token to pass through.
    @return: HTML output of results.
    '''
    tag_id = request.POST.get('tag_id')

    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        name = tag.name
    else:
        assert False, 'Must specify tag_id.'

    show_all = (request.POST['show_all'] == 'true')
    offset = int(request.POST.get('offset', 0))
    token = request.POST['token']
    # jobs_results, jobs_error, num_results = \
    #     _get_xplore_results(name, show_all=show_all, offset=offset,
    #                         sort=sort, sort_desc=sort_desc, ctype=ctype)
    tvUrl = "http://ieeetv.ieee.org/service/Signature" \
            "?url=http://ieeetv.ieee.org/service/VideosSearch?q=%s" % tag.name
    file2 = urllib2.urlopen(tvUrl).read()

    # get url from xml that is returned

    apixml = fromstring(file2)
    dev_url = apixml.find('url_dev').text

    try:
        tv_xml = fromstring(urllib2.urlopen(dev_url).read())

        results = tv_xml.findall('search-item')
        tvCount = len(results)

        tvHtml = ""
        for result in results:
            thumb = result.find('images').find('thumbnail').text
            title = result.find('title').text
            url = result.find('web-page').text
            tvHtml = tvHtml + '<img src="%s" height="60" width="105"/>' \
                              '<a href="%s" target="_blank">%s ' \
                              '<span class="popup newWinIcon">' \
                              '</span></a><br>\n' % (thumb, url, title)
    except:
        tvCount = 0
        tvHtml = ''

    # DEBUG:
    #xplore_error = 'BAD ERROR.'

    data = {
        'num_results': tvCount,
        'html': tvHtml,
        'search_term': name,
        'token': token,
    }

    return HttpResponse(json.dumps(data), 'application/javascript')


@csrf_exempt
def ajax_authors_results(request):
    '''
    Shows the list of IEEE xplore authors for the given tag.
    @param tag_id: POST var, specifyies the tag.
    @param token: POST var, the ajax token to pass through.
    @return: HTML output of results.
    '''
    tag_id = request.POST.get('tag_id')

    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        name = tag.name
    else:
        assert False, 'Must specify tag_id.'

    token = request.POST['token']

    # jobs_results, jobs_error, num_results = \
    #     _get_xplore_results(name, show_all=show_all, offset=offset,
    #                         sort=sort, sort_desc=sort_desc, ctype=ctype)

    authors, xplore_error, authorsCount = \
        ajax_xplore_authors(request.POST.get('tag_id'))

    authorsHtml = render_to_string('include_xplore_authors.html', {
        'xplore_results': authors
    })

    # DEBUG:
    #xplore_error = 'BAD ERROR.'

    data = {
        'num_results': authorsCount,
        'html': authorsHtml,
        'search_term': name,
        'token': token
    }

    return HttpResponse(json.dumps(data), 'application/javascript')


@login_required
def ajax_node(request):
    "Returns JSON data for the given node, including its parents."

    nodeId = request.GET['nodeId']
    node = Node.objects.get(id=nodeId)
    if len(node.parents.all()) == 0:
        parentName = None
    else:
        parentName = ', '.join([parent.name for parent in node.parents.all()])

    data = {
        'id': node.id,
        'name': node.name,
        'type': node.node_type.name,
        'num_resources': node.resources.count(),
    }

    if len(node.parents.all()) > 0:
        data['parents'] = []
        for parent in node.parents.all():
            data['parents'].append({
                'id': parent.id,
                'name': parent.name,
            })

    json1 = json.dumps(data, sort_keys=True, indent=4)

    return HttpResponse(json1, mimetype="text/plain")


@login_required
#@util.profiler
def ajax_textui_nodes(request):
    '''
    Returns HTML for the list of tags/clusters for the textui page.
    @param token: The unique token for this request, used in JS to ignore
                  overlapping AJAX requests.
    @param sector_id: (Optional) The sector to filter results.
    @param society_id: (Optional) The society to filter results.
    @param cluster_id: (Optional) The cluster to filter results,
                       used to filter "search_for" results.
    @param search_for: (Optional) A search phrase to filter results.
    @param sort: The sort method.
    @param page: The current tab/page ("sector" or "society").
    @param show_clusters: (Boolean)
    @param show_terms: (Boolean)
    @return: The HTML content for all results.
    '''
    log('ajax_textui_nodes()')
    token = request.GET['token']

    sector_id = request.GET.get('sector_id', None)
    if sector_id == '' or sector_id == 'null' or sector_id == 'all':
        sector_id = None
    try:
        sector_id = int(sector_id)
        sector = Node.objects.get(id=sector_id,
                                  node_type__name=NodeType.SECTOR)
    except (TypeError, ValueError):
        sector = None
    assert sector_id is None or type(sector_id) is int, \
        'Bad value for sector_id %r' % sector_id

    society_id = request.GET.get('society_id', None)
    if society_id == '' or society_id == 'null' or society_id == 'all':
        society_id = None
    try:
        society_id = int(society_id)
        society = Society.objects.get(id=society_id)
    except (TypeError, ValueError):
        society = None
    assert society_id is None or type(society_id) is int, \
        'Bad value for society_id %r' % society_id

    cluster_id = request.GET.get('cluster_id', None)
    if cluster_id == '' or cluster_id == 'null':
        cluster_id = None
    try:
        cluster_id = int(cluster_id)
        cluster = Node.objects.get(id=cluster_id,
                                   node_type__name=NodeType.TAG_CLUSTER)
    except (TypeError, ValueError):
        cluster = None
    assert cluster_id is None or type(cluster_id) is int, \
        'Bad value for cluster_id %r' % cluster_id

    search_for = request.GET.get('search_for', None)
    if search_for == 'null' or search_for == '':
        search_for = None

    show_clusters = request.GET.get('show_clusters', 'false')
    assert show_clusters in ['true', 'false'], \
        'show_clusters (%r) was not "true" or "false".' % (show_clusters)
    show_clusters = (show_clusters == 'true')

    assert show_clusters or settings.ENABLE_SHOW_CLUSTERS_CHECKBOX, \
        'Cannot show_clusters=false if ENABLE_SHOW_CLUSTERS_CHECKBOX ' \
        'is not set.'

    show_terms = request.GET.get('show_terms', 'false')
    assert show_terms in ['true', 'false'], \
        'show_terms (%r) was not "true" or "false".' % (show_terms)
    show_terms = (show_terms == 'true')

    assert show_terms or settings.ENABLE_SHOW_TERMS_CHECKBOX, \
        'Cannot set show_terms=false if ENABLE_SHOW_TERMS_CHECKBOX is not set.'

    #log('  sector_id: %s' % sector_id)
    #log('  society_id: %s' % society_id)
    #log('  cluster_id: %s' % cluster_id)
    #log('  search_for: %s' % search_for)
    #log('  show_clusters: %s' % show_clusters)
    #log('  show_terms: %s' % show_terms)
    #
    #log('  sector: %s' % sector)
    #log('  society: %s' % society)
    #log('  cluster: %s' % cluster)

    assert sector_id is None or society_id is None, \
        'Cannot specify both sector_id and society_id.'
    assert show_clusters or cluster_id is None, \
        'Cannot specify cluster_id and show_clusters=false.'

    sort = request.GET.get('sort')
    log('  sort: %s' % sort)

    page = request.GET['page']
    log('  page: %s' % page)
    if page != 'sector' and page != 'society':
        raise Exception('page (%r) should be "sector" or "society"' % page)

    #filterValues = request.GET.get('filterValues')
    ##log('filterValues: %s' % filterValues)

    log('')

    # Build the textui_flyover_url var.
    params = {}
    if sector_id is None:
        params['parent_id'] = 'null'
    else:
        params['parent_id'] = sector_id
    if society_id is None:
        params['society_id'] = 'null'
    else:
        params['society_id'] = society_id
    if search_for is not None:
        params['search_for'] = search_for.encode('utf-8')
    else:
        params['search_for'] = search_for
    params['page'] = page

    textui_flyovers_url = reverse('tooltip') + '/tagid?' + \
                          urllib.urlencode(params)
    # The tooltip url needs to know if 'all' societies or sectors is chosen.
    # Otherwise the color blocks in the tooltip will all be red.
    if request.GET.get('society_id', None) == "all":
        textui_flyovers_url = textui_flyovers_url.replace('society_id=null',
                                                          'society_id=all')
    if request.GET.get('sector_id', None) == "all":
        textui_flyovers_url = textui_flyovers_url.replace('parent_id=null',
                                                          'parent_id=all')

    # Get page from cache, or generate if needed.
    cache_params = {
        'sector_id': sector_id,
        'society_id': society_id,
        'cluster_id': cluster_id,
        'search_for': search_for,
        'sort': sort,
        'page': page,
        'show_clusters': show_clusters,
        'show_terms': show_terms,
    }

    if settings.DEBUG_IGNORE_CACHE:
        cache = None
    else:
        cache = Cache.objects.get('ajax_textui_nodes', cache_params)

    """ If there's no cache item found. Look for one that matches all
    params except with an empty search_for string (there should be
    many pre-populated ones). If we find that retrieve it and filter
    out all the items that don't match the search_for term. This will
    be considerably faster than hitting the DB."""
    if not cache and search_for:
        cache_params["search_for"] = "None"
        cache = Cache.objects.get('ajax_textui_nodes', cache_params)
        if cache:
            soup = BeautifulSoup(cache.content)
            non_matches = \
                soup.findAll('a', text=lambda text: search_for not in text)
            for nm in non_matches:
                if nm.findParent('div'):
                    nm.findParent('div').extract()
            cache = nm.join('')
        cache_params["search_for"] = search_for

    # Still no Cache so let's go to the DB.
    if not cache:
        # Create the cache if it doesn't already exist.
        print 'CACHE MISS: Creating new cache page.'
        content, node_count_content = _render_textui_nodes(
            sort, search_for, sector_id, sector, society_id, society,
            cluster_id, cluster, show_clusters, show_terms,
            request.user.is_staff, page)
        cache_content = json.dumps({
            'content': content,
            'node_count_content': node_count_content,
        })
        cache = Cache.objects.set('ajax_textui_nodes', cache_params,
                                  cache_content)
    else:
        #print 'CACHE HIT.'
        cache_content = json.loads(cache.content)
        content, node_count_content = cache_content['content'], \
                                      cache_content['node_count_content']

    return HttpResponse(json.dumps({
        'token': token,
        'search_for': search_for,
        'content': content,
        'node_count_content': node_count_content,
        'textui_flyovers_url': textui_flyovers_url,
    }), 'text/plain')


def get_nodes(query):  # todo: move this function to another place in future
    search_words = re.split(r'\s', query)

    queries = None
    for word in search_words:
        if queries is None:
            queries = Q(name__icontains=word)
        else:
            queries &= Q(name__icontains=word)

    return Node.objects.filter(queries)


def ajax_nodes_json(request):
    "Create a JSON collection for API"
    if not 's' in request.GET or not len(request.GET['s'].strip()):
        return HttpResponse("{'error': 'no search term provided'}",
                            content_type='application/javascript; '
                                         'charset=utf8')
    nodes = get_nodes(request.GET['s'])
    json = serializers.serialize("json", nodes, ensure_ascii=False,
                                 fields=('id', 'name'))
    json = json.replace(', "model": "ieeetags.node"', '')
    return HttpResponse(json,
                        content_type='application/javascript; charset=utf8')


def ajax_nodes_keywords(request):
    "Create a JSON collection for API"
    if not 'q' in request.GET or not len(request.GET['q'].strip()):
        return HttpResponse("{'error': 'no search term provided'}",
                            content_type='application/javascript; '
                                         'charset=utf8')
    nodes = get_nodes(request.GET['q'])

    values = ['{"value": %s}' % json.dumps(node.name) for node in nodes]
    result = "[%s]" % (", ".join(values))
    return HttpResponse(result,
                        content_type='application/json; charset=utf8')


@login_required
def ajax_nodes_xml(request):
    """Creates an XML list of nodes & connections for Asterisq Constellation
    Roamer."""

    #log('ajax_nodes_xml()')

    DEBUG_ROAMER_MAX_NODES = 40

    nodeId = request.GET['nodeId']
    #log('  url: ' + request.get_full_path())

    # TODO: the depth param is ignored, doesn't seem to affect anything now

    node = Node.objects.select_related('filters').get(id=nodeId)

    if node.node_type.name == NodeType.SECTOR:
        child_nodes = node.get_tags_and_clusters()
    else:
        child_nodes = node.child_nodes

    # NOTE: Can't use 'filters' in select_related() since it's a
    # many-to-many field.
    child_nodes = child_nodes.select_related('node_type').all()
    child_nodes = get_node_extra_info(child_nodes)

    # If parent node is a sector, filter the child tags
    valid_node_type = node.node_type.name == NodeType.SECTOR or \
                      node.node_type.name == NodeType.TAG_CLUSTER
    if valid_node_type:
        # Filter out any tags that don't have any societies
        childNodes1 = []

        for child_node in child_nodes:
            # List all clusters, plus any tags that have societies and
            # resoureces
            valid_node_type = child_node.node_type.name == NodeType.TAG_CLUSTER
            positive_nums = (child_node.num_societies1 > 0 and
                             child_node.num_resources1 > 0 and
                             child_node.num_filters1 > 0)
            if valid_node_type or positive_nums:
                childNodes1.append(child_node)
        child_nodes = childNodes1

    # The main node
    nodes = [node]

    # First sorting by connectedness here, so we get the X most connected nodes
    # (with the hard limit)
    child_nodes = Node.objects.sort_queryset_by_score(child_nodes, False)

    # Add the node's children
    # TODO: Number of child nodes is temporarily limited to a hard limit...
    # TODO: remove this later
    child_nodes = child_nodes[:DEBUG_ROAMER_MAX_NODES]

    nodes.extend(child_nodes)

    parent_nodes = []

    # The node's parent clusters
    exclude_sectors = []
    for cluster in node.get_parent_clusters():
        nodes.append(cluster)
        parent_nodes.append(cluster)

        for sector in cluster.parents.all():
            if sector not in exclude_sector:
                exclude_sectors.append(sector)

    # The node's parent sectors
    for sector in node.get_sectors():
        # Exclude a sector if this node is already in a cluster for that sector
        # ie. If 'node1' is in 'cluster1' in the 'Agriculture' sector,
        # don't show 'Agriculture'.
        if sector not in exclude_sectors:
            nodes.append(sector)
            parent_nodes.append(sector)

    # Get related tags for this tag
    related_tags = []
    if node.node_type.name == NodeType.TAG:
        for related_tag in node.related_tags.all():
            positive_counts = related_tag.filters.count() > 0 and \
                              related_tag.societies.count() > 0 and \
                              related_tag.resources.count() > 0
            if positive_counts:
                # Hide all tags with no societies or no resources
                related_tags.append(related_tag)
    nodes.extend(related_tags)

    # Edges

    edges = []

    for childNode in child_nodes:
        edges.append((node.id, childNode.id))

    for parent in parent_nodes:
        edges.append((parent.id, node.id))

    # Edges for related tags
    if node.node_type.name == NodeType.TAG:
        for related_tag in related_tags:
            edges.append((node.id, related_tag.id))

    # XML Output

    doc = xml.dom.minidom.Document()

    root = doc.createElement('graph_data')
    doc.appendChild(root)

    nodesElem = doc.createElement('nodes')
    root.appendChild(nodesElem)

    ROAMER_NODE_COLORS = {
        'selected': '#006599',
        'root': '#0000FF',
        'sector': '#FF0000',
        'tag_cluster': '#990099',
        'tag': '#00FF00',
    }
    GRAPHIC_BORDER_COLOR = '#bad4f9'

    #log('  nodes: %s' % len(nodes))
    #log('  edges: %s' % len(edges))

    for node1 in nodes:
        nodeElem = doc.createElement('node')
        nodeElem.setAttribute('id', str(node1.id))

        label = node1.name

        nodeElem.setAttribute('label', util.word_wrap(label, 25))
        nodeElem.setAttribute('depth_loaded', str(2))

        nodeElem.setAttribute('graphic_fill_color',
                              ROAMER_NODE_COLORS[node1.node_type.name])
        nodeElem.setAttribute('selected_graphic_fill_color',
                              ROAMER_NODE_COLORS[node1.node_type.name])
        nodeElem.setAttribute('graphic_border_color', GRAPHIC_BORDER_COLOR)
        nodeElem.setAttribute('graphic_type', 'shape')

        if node1.node_type.name == NodeType.ROOT:
            nodeElem.setAttribute('graphic_shape', 'circle')
            nodeElem.setAttribute('selected_graphic_shape', 'circle')
        elif node1.node_type.name == NodeType.SECTOR:
            nodeElem.setAttribute('graphic_shape', 'circle')
            nodeElem.setAttribute('selected_graphic_shape', 'circle')
        elif node1.node_type.name == NodeType.TAG_CLUSTER:
            nodeElem.setAttribute('graphic_shape', 'pentagon')
            nodeElem.setAttribute('selected_graphic_shape', 'pentagon')
        elif node1.node_type.name == NodeType.TAG:
            nodeElem.setAttribute('graphic_shape', 'square')
            nodeElem.setAttribute('selected_graphic_shape', 'square')
        else:
            raise Exception('Unknown node type "%s" for node "%s"' %
                            (node1.node_type.name, node1.name))

        # This takes up 40% page time
        filters = []
        for filter in node1.filters.all():
            filters.append(filter.value)

        # Add filters
        nodeElem.setAttribute('filter_groups', string.join(filters, ','))
        nodesElem.appendChild(nodeElem)

    edgesElem = doc.createElement('edges')
    root.appendChild(edgesElem)

    for edge in edges:
        edgeElem = doc.createElement('edge')
        edgeElem.setAttribute('id', str(edge[0]) + '-' + str(edge[1]))
        edgeElem.setAttribute('head_node_id', str(edge[0]))
        edgeElem.setAttribute('tail_node_id', str(edge[1]))
        edgesElem.appendChild(edgeElem)

    #if False:
    #    #log('XML: ----------')
    #    #log(doc.toprettyxml())
    #    #log('---------------')

    #return HttpResponse(doc.toprettyxml(), 'text/plain')
    return HttpResponse(doc.toprettyxml(), 'text/xml')


@csrf_exempt
@login_required
def ajax_notification_request(request):
    rnnr = ResourceAdditionNotificationRequest()
    action = request.POST['action']
    if action == 'enable':
        rnnr.email = request.POST['email']
        rnnr.date_created = datetime.datetime.now()
        rnnr.node = Node.objects.get(id=request.POST['nodeid'])
        try:
            rnnr.save()
        except:
            pass
        return HttpResponse('success')
    elif action == 'disable':
        email = request.POST['email']
        node = request.POST['nodeid']
        notifyRecord = ResourceAdditionNotificationRequest.objects.filter(node_id=node).get(email=email)
        notifyRecord.delete()
        return HttpResponse('success')
    else:
        return HttpResponse('failure')

@csrf_exempt
@login_required
def ajax_favorite_request(request):
    action = request.POST['action']
    member = User.objects.get(id=request.user.id)
    node_id = request.POST['nodeid']
    node = Node.objects.get(id=node_id)
    if action == 'enable':
        try:
            favorites = UserFavorites.objects.get(user=member)
            favorites.favorites.add(node)
        except UserFavorites.DoesNotExist:
            favorites_form = UserFavoriteForm(data=request.POST)
            favorites = favorites_form.save(commit=False)
            favorites.user = member
            favorites.save()
            favorites.favorites.add(node)
        return HttpResponse('success')
    elif action == 'disable':
        favorites = UserFavorites.objects.get(user=member)
        favorites.favorites.remove(node)
        return HttpResponse('success')
    else:
        return HttpResponse('failure')

@login_required
def tooltip(request, tag_id=None):
    'Returns the AJAX content for the tag tooltip/flyover in textui.'
    parent_id = request.GET.get('parent_id', None)
    society_id = request.GET.get('society_id', None)
    search_for = request.GET.get('search_for', None)
    page = request.GET.get('page', None)

    if tag_id is None:
        raise Exception('Must specify "tag_id".')

    def get_int_all_or_none(value):
        '''
        Converts the given value to an integer, the 'all' string, or None.
        Raises a ValueException if no conversion can be made.
        '''
        try:
            value = int(value)
            return value
        except (TypeError, ValueError):
            pass
        if hasattr(value, 'replace'):
            value = value.replace('"', '')
            value = value.replace("'", '')
        if value is None or value == 'null' or value == '':
            return None
        if value == 'all':
            return value
        raise ValueException('Unable to convert value %r' % value)

    society_id = get_int_all_or_none(society_id)
    parent_id = get_int_all_or_none(parent_id)

    #print '  tag_id: %r' % tag_id
    #print '  parent_id: %r' % parent_id
    #print '  search_for: %r' % search_for
    #print '  society_id: %r' % society_id

    if tag_id is not None:

        node = Node.objects.filter(id=tag_id)
        node = get_node_extra_info(node)
        node = single_row(node)

        #print '  node.node_type.name: %r' % node.node_type.name

        if node.node_type.name == NodeType.TAG:

            tag = node

            # Normal Tag

            if parent_id is not None:
                if parent_id == "all":
                    if not settings.DEBUG:
                        # Temporary fix for production since tooltip queries
                        # for 'all' are too slow
                        parent = Node.objects.filter(
                            node_type__name=NodeType.SECTOR)[0]
                        tags = parent.child_nodes
                    else:
                        node_type = Node.objects.getNodesForType(NodeType.ROOT)
                        parent = Node.objects.get(node_type=node_type)
                        tags = Node.objects.get_tags()
                else:
                    parent = Node.objects.get(id=parent_id)
                    tags = parent.child_nodes
                tags = get_node_extra_info(tags)
                tags = tags.values(
                    'num_filters1',
                    'num_related_tags1',
                    'num_resources1',
                    'num_sectors1',
                    'num_societies1',
                    'score1',
                )
                (min_resources, max_resources, min_sectors, max_sectors,
                 min_related_tags, max_related_tags, min_societies,
                 max_societies) = parent.get_sector_ranges(tags)
                (min_score, max_score) = \
                    parent.get_combined_sector_ranges(tags)

            elif society_id is not None:
                if society_id == 'all':
                    # Temporary fix for production since tooltip queries
                    # for 'all' are too slow
                    if not settings.DEBUG:
                        fake_society = Society.objects.all()[0]
                        (min_resources, max_resources, min_sectors,
                         max_sectors, min_related_tags, max_related_tags,
                         min_societies, max_societies) = \
                            fake_society.get_tag_ranges()
                        (min_score, max_score) = \
                            fake_society.get_combined_ranges()

                    else:
                        # For All Societies, check all tags to get mins/maxes.

                        tags = Node.objects.get_tags()
                        tags = get_node_extra_info(tags)

                        min_resources = None
                        max_resources = None
                        min_sectors = None
                        max_sectors = None
                        min_related_tags = None
                        max_related_tags = None
                        min_societies = None
                        max_societies = None
                        min_score = None
                        max_score = None
                        for tag1 in tags.values('num_resources1',
                                                'num_sectors1',
                                                'num_related_tags1',
                                                'num_societies1',
                                                'score1'):
                            if min_resources is None or \
                               tag1['num_resources1'] < min_resources:
                                min_resources = tag1['num_resources1']
                            if max_resources is None or \
                               tag1['num_resources1'] > max_resources:
                                max_resources = tag1['num_resources1']
                            if min_sectors is None or \
                               tag1['num_sectors1'] < min_sectors:
                                print "new min"
                                min_sectors = tag1['num_sectors1']
                            if max_sectors is None or \
                               tag1['num_sectors1'] > max_sectors:
                                print "new max"
                                max_sectors = tag1['num_sectors1']
                            if min_related_tags is None or \
                               tag1['num_related_tags1'] > min_related_tags:
                                min_related_tags = tag1['num_related_tags1']
                            if max_related_tags is None or \
                               tag1['num_related_tags1'] < max_related_tags:
                                max_related_tags = tag1['num_related_tags1']
                            if min_societies is None or \
                               tag1['num_societies1'] > min_societies:
                                min_societies = tag1['num_societies1']
                            if max_societies is None or \
                               tag1['num_societies1'] < max_societies:
                                max_societies = tag1['num_societies1']
                            if min_score is None or \
                               tag1['score1'] > min_score:
                                min_score = tag1['score1']
                            if max_score is None or tag1['score1'] < max_score:
                                max_score = tag1['score1']
                else:
                    society = Society.objects.get(id=society_id)
                    (min_resources, max_resources, min_sectors, max_sectors,
                     min_related_tags, max_related_tags, min_societies,
                     max_societies) = society.get_tag_ranges()
                    (min_score, max_score) = society.get_combined_ranges()

            elif search_for is not None:
                # Search for nodes with a phrase
                if len(search_for) >= 2:
                    search_words = re.split(r'\s', search_for)
                    queries = None
                    for word in search_words:
                        if queries is None:
                            queries = Q(name__icontains=word)
                        else:
                            queries &= Q(name__icontains=word)
                        # child_nodes = Node.objects.filter(
                    #     name__icontains=search_for,
                    #     node_type__name=NodeType.TAG)
                    child_nodes = \
                        Node.objects.filter(queries,
                                            node_type__name=NodeType.TAG)
                    filterIds = [filter.id for filter in Filter.objects.all()]
                    child_nodes = get_node_extra_info(child_nodes,
                                                              None, filterIds)
                else:
                    child_nodes = Node.objects.none()

                # Get the min/max for these search results
                # TODO: These don't account for filter==0, num_resources1==0,..
                min_score, max_score = util.get_min_max(child_nodes, 'score1')
                min_resources, max_resources = \
                    util.get_min_max(child_nodes, 'num_resources1')
                min_sectors, max_sectors = \
                    util.get_min_max(child_nodes, 'num_sectors1')
                min_related_tags, max_related_tags = \
                    util.get_min_max(child_nodes, 'num_related_tags1')
                min_societies, max_societies = \
                    util.get_min_max(child_nodes, 'num_societies1')

            else:
                # No sector/society/search phrase - could be in "All Sectors"
                # or "All Societies"
                assert False, "TODO"

            num_related_tags = tag.get_filtered_related_tag_count()
            num_societies = tag.societies.all()

            resourceLevel = _get_popularity_level(min_resources, max_resources,
                                                  tag.num_resources1)
            sectorLevel = _get_popularity_level(min_sectors, max_sectors,
                                                tag.num_sectors1)
            related_tag_level = _get_popularity_level(min_related_tags,
                                                      max_related_tags,
                                                      num_related_tags)
            society_level = _get_popularity_level(min_societies, max_societies,
                                                  tag.num_societies1)

            tagLevel = _get_popularity_level(min_score, max_score, node.score1)

            sectors_str = util.truncate_link_list(
                tag.get_sectors(),
                lambda item:
                '<a href="javascript:Tags.selectSector(%s);">%s</a>' %
                (item.id, item.name),
                lambda item: '%s' % item.name,
                TOOLTIP_MAX_CHARS,
                tag,
                'sector-tab'
            )

            related_tags_str = util.truncate_link_list(
                tag.related_tags.all(),
                lambda item:
                '<a href="javascript:Tags.selectTag(%s);">%s</a>' %
                (item.id, item.name),
                lambda item: '%s' % item.name,
                TOOLTIP_MAX_CHARS,
                tag,
                'related-tab'
            )

            # Filter out related tags without filters (to match roamer)
            related_tags2 = tag.related_tags.all()
            related_tags2 = get_node_extra_info(related_tags2)
            related_tags = []
            for related_tag in related_tags2:
                positive_nums = related_tag.num_filters1 > 0 and \
                                related_tag.num_resources1 > 0
                if positive_nums:
                    related_tags.append(related_tag)

            societies_str = util.truncate_link_list(
                tag.societies.all(),
                lambda item:
                '<a href="javascript:Tags.selectSociety(%s);">%s</a>' %
                (item.id, item.name),
                lambda item: '%s' % item.name,
                TOOLTIP_MAX_CHARS,
                tag,
                'society-tab'
            )

            show_edit_link = request.user.is_authenticated() and \
                             request.user.get_profile().role in \
                             (Profile.ROLE_SOCIETY_MANAGER, Profile.ROLE_ADMIN)

            if sectors_str == '':
                sectors_str = '<em class="none">(None)</em>'
            if societies_str == '':
                societies_str = '<em class="none">(None)</em>'
            if related_tags_str == '':
                related_tags_str = '<em class="none">(None)</em>'

            return render(request, 'tooltip.html', {
                'tag': tag,
                'tagLevel': tagLevel,
                'sectorLevel': sectorLevel,
                'relatedTagLevel': related_tag_level,
                'societyLevel': society_level,
                'sectors': sectors_str,
                'related_tags': related_tags_str,
                'societies': societies_str,
                'showEditLink': show_edit_link,
            })

        elif node.node_type.name == NodeType.TAG_CLUSTER:
            cluster = node

            tags = cluster.get_tags()

            if parent_id is not None and parent_id != 'all':
                tags = tags.filter(parents__id=parent_id)

            if page == 'sector':
                tab = 'sector-tab'
            elif page == 'society':
                tab = 'society-tab'
            else:
                raise Exception('Unknown page (%r)' % page)

            tags_str = util.truncate_link_list(
                tags,
                #lambda item: '<a href="javascript:Tags.selectTag(%s);">%s</a>'
                # % (item.id, item.name),
                lambda item: '%s' % item.name,
                lambda item: '%s' % item.name,
                TOOLTIP_MAX_CHARS,
                cluster,
                tab,
            )

            return render(request, 'tooltip_cluster.html', {
                'cluster': cluster,
                'tags': tags_str,
                'sector_id': parent_id,
            })

        else:
            raise Exception('Unknown node type "%s" for node "%s"' %
                            (node.node_type.name, node.name))

    else:
        assert False


def ajax_account(request, account_step):
    'Returns the HTML content for account lightboxs.'
    step = account_step
    if step == 'signin':
        return render(request, 'account_lightbox_signin.html')
    elif step == 'register':
        return render(request, 'account_lightbox_register.html')
    elif step == 'youraccount':
        member = request.user
        try:
            user_favorites = UserFavorites.objects.get(user=member)
            favorites = user_favorites.favorites.all()
            alerts = ResourceAdditionNotificationRequest.objects.filter(email=member.email).all()
        except UserFavorites.DoesNotExist:
            favorites = ''
            alerts = ''

        context_dict = {
            'favorites': favorites,
            'alerts': alerts
        }

        for alert in alerts:
            node_id = alert.node_id
            alert.node = Node.objects.get(id=node_id)

        return render(request, 'account_lightbox_youraccount.html', context_dict)

def ajax_video(request):
    'Returns the HTML content for the flash video.'
    return render(request, 'ajax_video.html')


def ajax_welcome(request):
    'Returns the HTML content for the welcome lightbox.'
    if request.path == '/textui_new':
        NEWUI = True
    else:
        NEWUI = False
    return render(request, 'ajax_welcome.html', {
        'NEWUI': NEWUI
    })


def ajax_profile_log(request):
    url = request.REQUEST['url']
    elapsed_time = request.REQUEST['elapsed_time']
    user_agent = request.META['HTTP_USER_AGENT']
    plog = ProfileLog()
    plog.url = url
    plog.elapsed_time = elapsed_time
    plog.user_agent = user_agent
    plog.save()
    return HttpResponse('success')


def ajax_javascript_error_log(request):
    #print 'ajax_javascript_error_log()'
    message = request.REQUEST['message']
    url = request.REQUEST['url']
    vars = request.REQUEST['vars']

    #print '  message: %r' % message
    #print '  url: %r' % url
    #print '  vars: %r' % vars
    vars = util.urldecode(vars)
    #print '  vars: %r' % vars

    s = []
    for name in sorted(vars.keys()):
        s.append('%s=%r' % (name, vars[name]))
    s = '\n'.join(s)

    util.send_admin_email('JAVASCRIPT ERROR: %s' % message, '''URL: %s

%s''' % (url, s))

    return HttpResponse('success')


def _render_textui_nodes(sort, search_for, sector_id, sector, society_id,
                         society, cluster_id, cluster, show_clusters,
                         show_terms, is_staff, page):
    order_by = None
    extra_order_by = None
    search_page_title = None

    if sort is None or sort == 'alphabetical':
        order_by = 'name'
    elif sort == 'frequency':
        order_by = '-num_resources1'
    elif sort == 'num_sectors':
        extra_order_by = ['-num_sectors1', 'name']
    elif sort == 'num_related_tags':
        extra_order_by = ['-num_related_tags1', 'name']
    #elif sort == 'clusters_first_alpha':
    #    # See below
    #    pass
    elif sort == 'connectedness':
        extra_order_by = ['-score1', 'name']
    elif sort == 'num_societies':
        extra_order_by = ['num_societies1', 'name']
    else:
        raise Exception('Unrecognized sort "%s"' % sort)

    # TODO: Filters disabled for now
    #filterIds = []
    #if filterValues != '' and filterValues is not None:
    #    for filterValue in filterValues.split(','):
    #        filterIds.append(Filter.objects.getFromValue(filterValue).id)
    # TODO: Just select all filters for now
    filterIds = [filter.id for filter in Filter.objects.all()]

    search_for_too_short = False

    num_tags = 0
    num_clusters = 0

    def and_query(query1, query2):
        if query1 is not None:
            return query1 & query2
        else:
            return query2

    def or_query(query1, query2):
        if query1 is not None:
            return query1 | query2
        else:
            return query2

    word_queries = None
    if search_for is not None:
        # Search for nodes with a phrase
        # NOTE: <= 2 char searches take a long time (2-3 seconds),
        # vs 200ms average for anything longer

        # Require >= 3 chars for general search, or >= 2 chars
        # for in-node/in-society search.
        ids_not_none = (sector_id is not None or society_id is not None)
        if len(search_for) >= 3 or (len(search_for) >= 2 and ids_not_none):
            # Search phrase was long enough.
            log('  Searching by keyword %r' % search_for)

            search_words = re.split(r'\s', search_for)
            #log('search_words: %s' % search_words)

            or_flag = False
            for word in search_words:
                if word != '':
                    #log('  word: %r' % word)
                    log('  word: %r' % word)
                    if word == 'OR':
                        or_flag = True
                        continue

                    if or_flag:
                        word_queries = or_query(word_queries,
                                                Q(name__icontains=word))
                        or_flag = False
                    else:
                        word_queries = and_query(word_queries,
                                                 Q(name__icontains=word))

        else:
            # Search phrase was too short, return empty results.
            child_nodes = Node.objects.none()
            search_for_too_short = True

    if search_for_too_short:
        child_nodes = Node.objects.none()
    else:
        # Start filtering the nodes.
        child_nodes = Node.objects.all()

    if word_queries:
        child_nodes = child_nodes.filter(word_queries)

    if sector:
        # Search within a sector.
        #log('  searching by sector %r' % sector_id)
        child_nodes = child_nodes.filter(parents__id=sector_id)

    elif society:
        # Search within a society.
        #log('  searching by society %r' % society_id)
        child_nodes = child_nodes.filter(societies__id=society_id)

    if cluster:
        # Search within a cluster (in addition to any sector/society
        # filtering above).
        #log('  searching by cluster %r' % cluster_id)
        child_nodes = child_nodes.filter(parents__id=cluster_id)

    if show_clusters:
        # Restrict to only tags & clusters.
        child_nodes = \
            child_nodes.filter(Q(node_type__name=NodeType.TAG) |
                               Q(node_type__name=NodeType.TAG_CLUSTER))
    else:
        # Restrict to only tags.
        child_nodes = child_nodes.filter(node_type__name=NodeType.TAG)
    child_nodes = get_node_extra_info(child_nodes, extra_order_by,
                                              filterIds)
    print child_nodes.query
    if word_queries:
        log('  using min/max for all results.')
        # Get the min/max scores for these search results
        min_score = None
        max_score = None
        min_cluster_score = None
        max_cluster_score = None

        for node1 in child_nodes:
            if node1.node_type.name == NodeType.TAG_CLUSTER:
                if min_cluster_score is None:
                    min_cluster_score = node1.score1
                else:
                    min_cluster_score = min(min_cluster_score, node1.score1)
                if max_cluster_score is None:
                    max_cluster_score = node1.score1
                else:
                    max_cluster_score = max(max_cluster_score, node1.score1)
            else:
                if min_score is None:
                    min_score = node1.score1
                else:
                    min_score = min(min_score, node1.score1)
                if max_score is None:
                    max_score = node1.score1
                else:
                    max_score = max(max_score, node1.score1)
    # todo: rename "some_condition" to understandable name
    some_condition = (cluster and show_terms and not word_queries and
                      sector is None and society is None)
    if show_terms and (word_queries or some_condition):
        # Show empty terms if we're:
        # 1. Searching by phrase, or
        # 2. Searching within a cluster, but not in any sector/society.
        show_empty_terms = True
    else:
        show_empty_terms = False

    if cluster:
        # Get min/max scores for this cluster.
        #log('  getting min/max for this cluster.')
        (min_resources, max_resources, min_sectors, max_sectors,
         min_related_tags, max_related_tags, min_societies, max_societies) = \
            cluster.get_sector_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = \
            cluster.get_combined_sector_ranges(
                show_empty_terms=show_empty_terms)
    elif sector:
        # Get min/max scores for this sector.
        #log('  getting min/max for this sector.')
        (min_resources, max_resources, min_sectors, max_sectors,
         min_related_tags, max_related_tags, min_societies, max_societies) = \
            sector.get_sector_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = \
            sector.get_combined_sector_ranges(
                show_empty_terms=show_empty_terms)
    elif society:
        # Get min/max scores for this society.
        #log('  getting min/max for this society.')
        (min_resources, max_resources, min_sectors, max_sectors,
         min_related_tags, max_related_tags, min_societies, max_societies) = \
            society.get_tag_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = \
            society.get_combined_ranges(show_empty_terms=show_empty_terms)
    else:
        # Get min/max scores for all tags/clusters (root node).
        #log('  getting min/max for root node.')
        if sector_id is None and society_id is None:
            root_node = Node.objects.get(node_type__name=NodeType.ROOT)
            (min_score, max_score) = \
                root_node.get_combined_sector_ranges(
                    show_empty_terms=show_empty_terms)
        else:
            min_score = 0
            max_score = 10000
            min_cluster_score = 0
            max_cluster_score = 10000

    min_cluster_score = 0
    max_cluster_score = 1
    for node1 in child_nodes:
        if node1.node_type.name == NodeType.TAG_CLUSTER:
            if min_cluster_score is None:
                min_cluster_score = node1.score1
            else:
                min_cluster_score = min(min_cluster_score, node1.score1)
                if max_cluster_score is None:
                    max_cluster_score = node1.score1
                else:
                    max_cluster_score = max(max_cluster_score, node1.score1)


    #log('  min_resources: %s' % min_resources)
    #log('  max_resources: %s' % max_resources)
    #log('  min_score: %s' % min_score)
    #log('  max_score: %s' % max_score)
    #log('  min_cluster_score: %s' % min_cluster_score)
    #log('  max_cluster_score: %s' % max_cluster_score)

    if show_clusters:
        if cluster is None and not word_queries:
            # Exclude clustered tags.
            log('  Excluding clustered tags.')
            child_nodes = \
                child_nodes.exclude(
                    parents__node_type__name=NodeType.TAG_CLUSTER)

    if order_by is not None:
        # Sort by one of the non-extra columns
        child_nodes = child_nodes.order_by(order_by)

    # This saves time when we check child_node.node_type later on
    # (prevents DB hit for every single child_node)
    child_nodes = child_nodes.select_related('node_type')

    # remove 'False and' below to enable the term count (for staff only) 
    if False and is_staff:
        num_terms = child_nodes.filter(is_taxonomy_term=True).count()
    else:
        num_terms = None

    clusters = []
    child_nodes2 = []

    if child_nodes.count() > 0:
        for child_node in child_nodes.values('id', 'name', 'node_type__name',
                                             'num_related_tags1',
                                             'num_resources1',
                                             'num_sectors1', 'num_societies1',
                                             'score1', 'is_taxonomy_term'):
            filter_child_node = False

            # TODO: This is too slow, reenable later
            #num_related_tags = child_node['get_filtered_related_tag_count']()
            num_related_tags = child_node['num_related_tags1']

            if child_node['node_type__name'] == NodeType.TAG:

                # Show all terms, and all tags with content.
                # if (show_empty_terms and child_node['is_taxonomy_term']) or
                #         (child_node['num_selected_filters1'] > 0 and
                #          child_node['num_societies1'] > 0 and
                #          child_node['num_resources1'] > 0):
                if (show_empty_terms and child_node['is_taxonomy_term']) or \
                        (child_node['num_societies1'] > 0 ):

                    try:
                        combinedLevel = \
                            _get_popularity_level(min_score, max_score,
                                                  child_node['score1'],
                                                  node=child_node)
                    except Exception:
                        print 'Exception during _get_popularity_level() ' \
                              'for node %r (%r), type %r' % \
                              (child_node['name'], child_node['id'],
                               child_node['node_type__name'])
                        print "child_node['id']: %s" % child_node['id']
                        print "child_node['node_type__name']: %s" % \
                              child_node['node_type__name']
                        print "child_node['num_societies1']: %s" % \
                              child_node['num_societies1']
                        print "child_node['num_resources1']: %s" % \
                              child_node['num_resources1']
                        print "child_node['score1']: %s" % child_node['score1']
                        raise

                    # Combined scores
                    child_node['score'] = child_node['score1']
                    child_node['level'] = combinedLevel

                    #print 'combinedLevel: %s' % combinedLevel

                    #child_node['min_score'] = min_score
                    #child_node['max_score'] = max_score

                else:
                    #log('removing node %s' % child_node['name'])
                    #log('  child_node['num_selected_filters1']: %s'
                    # % child_node['num_selected_filters1'])
                    #log('  child_node['num_societies1']: %s'
                    # % child_node['num_societies1'])
                    #log('  child_node['num_resources1']: %s'
                    # % child_node['num_resources1'])
                    filter_child_node = True

            elif child_node['node_type__name'] == NodeType.TAG_CLUSTER:
                # Only show clusters that have one of the selected filters
                #if child_node['filters'].filter(id__in=filterIds).count():
                #    cluster_child_tags = child_node['get_tags']()
                #    cluster_child_tags = \
                #        get_node_extra_info(cluster_child_tags)
                #    
                #    # Find out how many of this cluster's child tags would
                #    # show with the current filters
                #    num_child_tags = 0
                #    for cluster_child_tag in cluster_child_tags:
                #        if cluster_child_tag.num_resources1 > 0 and
                #           cluster_child_tag.num_societies1 > 0 and
                #           cluster_child_tag.num_filters1 > 0 and
                #           cluster_child_tag.filters.filter(id__in=filterIds)\
                #                            .count() > 0:
                #            num_child_tags += 1
                #    
                #    if num_child_tags > 0:
                #        # do nothing
                #        pass
                #    else:
                #        filter_child_node = True

                # TODO: Not using levels yet, so all clusters show as the same
                # color.
                #
                #child_node['level'] = ''

                # (min_score, max_score) = \
                #     child_nodes.get(id=child_node['id']).\
                #         get_combined_sector_ranges(
                #             show_empty_terms=show_empty_terms)
                child_node['level'] = \
                    _get_popularity_level(min_cluster_score, max_cluster_score,
                                          child_node['score1'],
                                          node=child_node)

                # Make sure clusters show on top of the list.
                filter_child_node = True
                clusters.append(child_node)


            else:
                raise Exception('Unknown child node type "%s" for node "%s"' %
                                (child_node['node_type__name'],
                                 child_node['name']))

            if not filter_child_node:
                child_nodes2.append(child_node)

    num_clusters = len(clusters)
    num_tags = len(child_nodes2)

    child_nodes = clusters + child_nodes2

    search_length = 0

    if search_for is not None:
        final_punc = ('.', ':')[len(child_nodes) > 0]
        search_length = len(search_for)
        str = ''
        if cluster_id is not None:
            str += ' in the topic area "%s"' % (cluster.name)
        if sector_id is not None:
            str += ' in the industry sector "%s"' % (sector.name)
        elif society_id is not None:
            str += ' in the organization "%s"' % (society.name)

        str += final_punc

        search_page_title = {"num": len(child_nodes), "search_for": search_for,
                             "node_desc": str}

    #log('  num_clusters: %s' % num_clusters)
    #log('  num_tags: %s' % num_tags)
    #log('    # real tags: %s' % len(child_nodes2))

    if not society:
        try:
            society = Society.objects.get(id=society_id)
        except Society.DoesNotExist:
            society = None

    no_results = False

    if not num_clusters and not num_tags:
        no_results = True

    content = render_to_string('ajax_textui_nodes.html', {
        'child_nodes': child_nodes,
        'sector_id': sector_id,
        'society_id': society_id,
        'search_for': search_for,
        'search_for_too_short': search_for_too_short,
        'search_page_title': search_page_title,
        'num_tags': num_tags,
        'num_clusters': num_clusters,
        'cluster_id': cluster_id,
        'cluster': cluster,
        'page': page,
        'society': society,
        'search_length': search_length
    })

    node_count_content = render_to_string('ajax_textui_node_count.inc.html', {
        'child_nodes': child_nodes,
        'num_clusters': num_clusters,
        'num_tags': num_tags,
        'search_for': search_for,
        'search_for_too_short': search_for_too_short,
        'search_page_title': search_page_title,
        'cluster': cluster,
        'num_terms': num_terms,
        'sector': sector,
        'society': society,
        'no_results': no_results,
    })

    return [content, node_count_content]


_POPULARITY_LEVELS = [
    'level1',
    'level2',
    'level3',
    'level4',
    'level5',
    'level6',
]


def _get_popularity_level(min, max, count, node=None):
    '''
    Gets the popularity level for the given count of items.
    
    For example, if we are looking at all tags for a given sector,
    then we find the min/max number of related tags is 1 and 10 respectively.
    Then we can call this function for each tag with params (1, 10, count)
    where count is the number of related tags for each tag,
    and we'll get a popularity level for each tag.
    
    @param min: The minimum count for all other peer items.
    @param max: The maximum count for all other peer items.
    @param count: The count for this specific item.
    @return: A text label 'level1' through 'level6'.
    '''

    min = min or 0

    if count < min or count > max:
        body = []
        if node:
            body.append('Node:')
            body.append('  id: %s' % node['id'])
            body.append('  name: %s' % node['name'])
            body.append('  score1: %s' % node['score1'])
        body = '\n'.join(body)
        # util.send_admin_email('Error in _get_popularity_level():'
        #                       ' count %r is outside the range (%r, %r)' %
        #                       (count, min, max), body)
        # raise Exception('count %r is outside of the min/max range (%r, %r)' %
        #                 (count, min, max) + '\n' + body)

    # NOTE: This is just to prevent errors for the end-user.
    if count < min:
        count = min
    elif count > max:
        count = max

    if min == max:
        return _POPULARITY_LEVELS[len(_POPULARITY_LEVELS) - 1]
    print "%s, %s, %s" % (min, max, count)

    level = int(math.ceil(float(count - min) / float(max - min) *
                          float(len(_POPULARITY_LEVELS) - 1))) + 1

    # TODO: This fixes invisible terms where count is < min. Is this a hack?
    if level == 0:
        level = 1

    return 'level' + str(level)
