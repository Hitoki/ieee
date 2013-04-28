import cgi
import datetime
from django.db.models import Count, Q
from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson as json
from logging import debug as log
import os.path
import re
import string
import sys
import time
import traceback
from urllib import quote
import urllib
import urllib2
import xml.dom.minidom
from decorators import optional_login_required as login_required

from django.middleware import csrf
from django.views.decorators.csrf import csrf_exempt

from ieeetags.models import single_row, Cache, Filter, Node, NodeType, Profile, Resource, ResourceType, Society, ProfileLog, ResourceAdditionNotificationRequest
from ieeetags.forms import *
#from profiler import Profiler
import settings
import util
from widgets import make_display_only
from BeautifulSoup import BeautifulSoup

from .xplore import _get_xplore_results

TOOLTIP_MAX_CHARS = 120

def render(request, template, dictionary=None):
    "Use this instead of 'render_to_response' to enable custom context processors, which add things like MEDIA_URL to the page automatically."
    return render_to_response(template, dictionary=dictionary, context_instance=RequestContext(request))

# ------------------------------------------------------------------------------

def error_view(request):
    '''
    Custom error view for production servers.  Sends an email to admins for every error with a traceback.
    
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
    'Displays "site disabled" message when the entire site is disabled (settings.DISABLE_SITE == True).'
    return render(request, 'site_disabled.html', {
    })
    
@login_required
def index(request):
    if request.META['HTTP_HOST'].startswith('m.'):
        return render_to_response('index_mobile.html', {}, context_instance=RequestContext(request))
    'Redirects user to textui page.'
    return HttpResponseRedirect(reverse('textui'))

@login_required
def roamer(request):
    'Shows the Asterisq Constellation Roamer flash UI.'
    nodeId = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId':nodeId,
        'sectors':sectors,
        'filters':filters,
    })

@login_required
def textui(request, survey=False):
    'Shows the textui (aka. Tag Galaxy) UI.'
    nodeId = request.GET.get('nodeId', None)
    sectorId = None
    clusterId = None
    
    # If url ends with /survey set a session var so we can display an additional banner.
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
    
    if request.path == '/textui_new':
        template = 'textui_new.html'
        NEWUI = True
        newui_search_button = False
    else:
        template = 'textui.html'
        NEWUI = False
        newui_search_button = settings.ENABLE_SEARCH_BUTTON

    return render(request, template, {
        'sectorId':sectorId,
        'clusterId': clusterId,
        'sectors':sectors,
        'filters':filters,
        'societies':societies,
        'ENABLE_SHOW_CLUSTERS_CHECKBOX': settings.ENABLE_SHOW_CLUSTERS_CHECKBOX,
        'ENABLE_SHOW_TERMS_CHECKBOX': settings.ENABLE_SHOW_TERMS_CHECKBOX,
        'ENABLE_SEARCH_BUTTON': settings.ENABLE_SEARCH_BUTTON,
        'SEARCH_KEY_DELAY': settings.SEARCH_KEY_DELAY,
        'NEWUI':NEWUI,
        'ENABLE_SEARCH_BUTTON': newui_search_button
    })

@login_required
def textui_home(request):
    'Shows textui "home" AJAX page.'
    return render(request, 'textui_home.html')

@login_required
def textui_help(request):
    'Shows textui "help" AJAX page.'
    return render(request, 'textui_help.html')

@login_required
def feedback(request):
    'User feedback page.  When submitted, sends an email to all admins.'
    if request.method == 'GET':
        if request.user.is_authenticated and not request.user.is_anonymous:
            form = FeedbackForm(
                initial={
                    'name': '%s %s' % (request.user.first_name, request.user.last_name),
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
            message = 'Sent on %s:\n%s\n\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), form.cleaned_data['comments'])
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
    'Shows the AJAX browser compatability warning page.  Allows the user to click through if they still want to browse the site.'
    return render(request, 'browser_warning.html')
    
def tester_message(request):
    'Returns the HTML content for the tester message.'
    return render(request, 'tester_message.html')

def tester_survey(request):
    'Returns the HTML content for the tester survey.'
    return render(request, 'tester_survey.html')

import hotshot
import os
import time
import settings

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
    
    For example, if we are looking at all tags for a given sector, then we find the min/max number of related tags is 1 and 10 respectively.  Then we can call this function for each tag with params (1, 10, count) where count is the number of related tags for each tag, and we'll get a popularity level for each tag.
    
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
        util.send_admin_email('Error in _get_popularity_level(): count %r is outside the range (%r, %r)' % (count, min, max), body)
        #raise Exception('count %r is outside of the min/max range (%r, %r)' % (count, min, max) + '\n' + body)
    
    # NOTE: This is just to prevent errors for the end-user.
    if count < min:
        count = min
    elif count > max:
        count = max
    
    if min == max:
        return _POPULARITY_LEVELS[len(_POPULARITY_LEVELS)-1]
    print "%s, %s, %s" % (min, max, count)
    import math
    level = int(math.ceil(float(count-min) / float(max-min) * float(len(_POPULARITY_LEVELS)-1))) + 1
    
    # TODO: This fixes invisible terms where the count is < min.  Is this a hack?
    if level == 0:
        level = 1
    
    return 'level' + str(level)

def _render_textui_nodes(request, sort, search_for, sector_id, sector, society_id, society, cluster_id, cluster, show_clusters, show_terms, is_staff, page):

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
        # NOTE: <= 2 char searches take a long time (2-3 seconds), vs 200ms average for anything longer
        
        # Require >= 3 chars for general search, or >= 2 chars for in-node/in-society search.
        if len(search_for) >= 3 or (len(search_for) >= 2 and (sector_id is not None or society_id is not None)):
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
                        word_queries = or_query(word_queries, Q(name__icontains=word))
                        or_flag = False
                    else:
                        word_queries = and_query(word_queries, Q(name__icontains=word))
                
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
        # Search within a cluster (in addition to any sector/society filtering above).
        #log('  searching by cluster %r' % cluster_id)
        child_nodes = child_nodes.filter(parents__id=cluster_id)
        
    if show_clusters:
        # Restrict to only tags & clusters.
        child_nodes = child_nodes.filter(Q(node_type__name=NodeType.TAG) | Q(node_type__name=NodeType.TAG_CLUSTER))
    else:
        # Restrict to only tags.
        child_nodes = child_nodes.filter(node_type__name=NodeType.TAG)
    child_nodes = Node.objects.get_extra_info(child_nodes, extra_order_by, filterIds)
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

    if show_terms and (word_queries or (cluster and show_terms and not word_queries and sector is None and society is None)):
        # Show empty terms if we're:
        # 1. Searching by phrase, or
        # 2. Searching within a cluster, but not in any sector/society.
        show_empty_terms = True
    else:
        show_empty_terms = False
    
    if cluster:
        # Get min/max scores for this cluster.
        #log('  getting min/max for this cluster.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = cluster.get_sector_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = cluster.get_combined_sector_ranges(show_empty_terms=show_empty_terms)
    elif sector:
        # Get min/max scores for this sector.
        #log('  getting min/max for this sector.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = sector.get_sector_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = sector.get_combined_sector_ranges(show_empty_terms=show_empty_terms)
    elif society:
        # Get min/max scores for this society.
        #log('  getting min/max for this society.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = society.get_tag_ranges(show_empty_terms=show_empty_terms)
        (min_score, max_score) = society.get_combined_ranges(show_empty_terms=show_empty_terms)
    else:
        # Get min/max scores for all tags/clusters (root node).
        #log('  getting min/max for root node.')
        if sector_id is None and society_id is None:
            root_node = Node.objects.get(node_type__name=NodeType.ROOT)
            (min_score, max_score) = root_node.get_combined_sector_ranges(show_empty_terms=show_empty_terms)
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
            child_nodes = child_nodes.exclude(parents__node_type__name=NodeType.TAG_CLUSTER)
    
    
    if order_by is not None:
        # Sort by one of the non-extra columns
        child_nodes = child_nodes.order_by(order_by)
    
    # This saves time when we check child_node.node_type later on (prevents DB hit for every single child_node)
    child_nodes = child_nodes.select_related('node_type')
    
    # remove 'False and' below to enable the term count (for staff only) 
    if False and is_staff:
        num_terms = child_nodes.filter(is_taxonomy_term=True).count()
    else:
        num_terms = None
    
    clusters = []
    child_nodes2 = []
    
    
    if child_nodes.count() > 0:
        for child_node in child_nodes.values(
            'id',
            'name',
            'node_type__name',
            'num_related_tags1',
            'num_resources1',
            'num_sectors1',
            'num_societies1',
            'score1',
            'is_taxonomy_term',
        ):
            filter_child_node = False
            
            # TODO: This is too slow, reenable later
            #num_related_tags = child_node['get_filtered_related_tag_count']()
            num_related_tags = child_node['num_related_tags1']
            
            if child_node['node_type__name'] == NodeType.TAG:
                
                # Show all terms, and all tags with content.
                #if (show_empty_terms and child_node['is_taxonomy_term']) or (child_node['num_selected_filters1'] > 0 and child_node['num_societies1'] > 0 and child_node['num_resources1'] > 0):
                if (show_empty_terms and child_node['is_taxonomy_term']) or (child_node['num_societies1'] > 0 and child_node['num_resources1'] > 0):
                    
                    try:
                        combinedLevel = _get_popularity_level(min_score, max_score, child_node['score1'], node=child_node)
                    except Exception:
                        print 'Exception during _get_popularity_level() for node %r (%r), type %r' % (child_node['name'], child_node['id'], child_node['node_type__name'])
                        print "child_node['id']: %s" % child_node['id']
                        print "child_node['node_type__name']: %s" % child_node['node_type__name']
                        print "child_node['num_societies1']: %s" % child_node['num_societies1']
                        print "child_node['num_resources1']: %s" % child_node['num_resources1']
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
                    #log('  child_node['num_selected_filters1']: %s' % child_node['num_selected_filters1'])
                    #log('  child_node['num_societies1']: %s' % child_node['num_societies1'])
                    #log('  child_node['num_resources1']: %s' % child_node['num_resources1'])
                    filter_child_node = True
                    
                    
            elif child_node['node_type__name'] == NodeType.TAG_CLUSTER:
                # Only show clusters that have one of the selected filters
                #if child_node['filters'].filter(id__in=filterIds).count():
                #    cluster_child_tags = child_node['get_tags']()
                #    cluster_child_tags = Node.objects.get_extra_info(cluster_child_tags)
                #    
                #    # Find out how many of this cluster's child tags would show with the current filters
                #    num_child_tags = 0
                #    for cluster_child_tag in cluster_child_tags:
                #        if cluster_child_tag.num_resources1 > 0 and cluster_child_tag.num_societies1 > 0 and cluster_child_tag.num_filters1 > 0 and cluster_child_tag.filters.filter(id__in=filterIds).count() > 0:
                #            num_child_tags += 1
                #    
                #    if num_child_tags > 0:
                #        # do nothing
                #        pass
                #    else:
                #        filter_child_node = True
                
                # TODO: Not using levels yet, so all clusters show as the same color.
                #child_node['level'] = ''
                
                #(min_score, max_score) = child_nodes.get(id=child_node['id']).get_combined_sector_ranges(show_empty_terms=show_empty_terms)
                child_node['level'] = _get_popularity_level(min_cluster_score, max_cluster_score, child_node['score1'], node=child_node)
                
                # Make sure clusters show on top of the list.
                filter_child_node = True
                clusters.append(child_node)
                
                    
            else:
                raise Exception('Unknown child node type "%s" for node "%s"' % (child_node['node_type__name'], child_node['name']))
            
            if not filter_child_node:
                child_nodes2.append(child_node)
    
    num_clusters = len(clusters)
    num_tags = len(child_nodes2)
    
    child_nodes = clusters + child_nodes2
    
    search_length = 0

    if search_for is not None:
        final_punc =  ('.', ':')[len(child_nodes) > 0]
        search_length = len(search_for)
        str = ''
        if cluster_id is not None:
            str += ' in the topic area "%s"' % (cluster.name)
        if sector_id is not None:
            str += ' in the industry sector "%s"' % (sector.name)
        elif society_id is not None:
            str += ' in the organization "%s"' % (society.name)
        
        str += final_punc
        
        search_page_title = {"num": len(child_nodes), "search_for": search_for, "node_desc": str}
    
    #log('  num_clusters: %s' % num_clusters)
    #log('  num_tags: %s' % num_tags)
    #log('    # real tags: %s' % len(child_nodes2))
    
    if not society:
        try:
            society = Society.objects.get(id=society_id)
        except Society.DoesNotExist:
            society = None

    if request.META['HTTP_REFERER'].endswith('/textui_new'):
        NEWUI = True
    else:
        NEWUI = False

    from django.template.loader import render_to_string
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
        'NEWUI': NEWUI,
    })
    
    return [content, node_count_content]

def tags_list(request):
    '''
    Displays a list of links to the tag "wikipedia-style" pages (see views.tag_landing)
    Mostly useful for spider link discovery and SEO.
    '''

    is_staff = request.user.is_staff

    return render_to_response('tags_list.html', {"tags": Node.objects.get_tags(), "show_id": is_staff, "show_resource_count": is_staff, "show_checkbox": is_staff }, context_instance=RequestContext(request));
    
def tags_all(request):
    '''
    Displays a list of "high_potency" links to the tag "wikipedia-style" pages (see views.tag_landing)
    '''

    nodes = Node.objects.filter(high_potency=True)

    return render_to_response('tags_all.html', {"tags": nodes }, context_instance=RequestContext(request))

def tags_starts(request, starts_with):
    nodes = Node.objects.filter(high_potency=False, name__iregex='^'+starts_with)
    return render_to_response('tags_list.html', {"tags": nodes }, context_instance=RequestContext(request))

def tag_landing(request, tag_id):
    '''
    Displays a wikipedia-style "flat" view of the tag. No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    '''
    # TODO move logic to decorator
    if re.match(settings.MOBILE_URL_PREFIX, request.META['HTTP_HOST']) and not ('nomobile' in request.GET and request.GET['nomobile']=="1"):
        template_name = 'tag_landing_mobile.html'
    else:
        template_name = 'tag_landing.html'
    return print_resource(request, tag_id, 'all', template_name=template_name, create_links=True, toc=True)
    
def clusters_list(request):
    '''
    Displays a wikipedia-style "flat" view of the cluster.
    '''
    return render(request, 'clusters_list.html', {
        'clusters': Node.objects.get_clusters(),
    })

def cluster_landing(request, cluster_id):
    '''
    Displays a wikipedia-style "flat" view of the cluster. No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    '''
    return print_resource(request, cluster_id, 'all', template_name='cluster_landing.html', create_links=True, toc=True)
    
def print_resource(request, tag_id, resource_type, template_name='print_resource.html', create_links=False, toc=False):
    '''
    The print resource page.
    
    @param tag_id: The tag to print results for.
    @param resource_type: Which resource(s) to include.
    '''
    
    tag = Node.objects.get(id=tag_id)
    
    sectors = Node.objects.none()
    related_tags = Node.objects.none()
    societies = Society.objects.none()
    conferences = Node.objects.none()
    patents = resource_type == 'patents' or resource_type == 'all'
    periodicals = Node.objects.none()
    standards = Node.objects.none()
    jobsHtml = ''
    conf_count = 0
    totalfound = 0
    xplore_edu_results = None
    totaledufound = 0
    xplore_results = None
    
    if resource_type not in ['all', 'sectors', 'related_tags', 'societies', 'conferences', 'periodicals', 'standards', 'xplore_edu', 'xplore', 'jobs', 'patents','overview']:
        raise Exception('Unknown resource_type "%s"' % resource_type)

    if resource_type == 'sectors' or resource_type == 'all':
        # TODO: Need to filter clusters out here?
        sectors = tag.parents.all()
    if resource_type == 'related_tags' or resource_type == 'all':
        related_tags = tag.related_tags.all()
    if resource_type == 'societies' or resource_type == 'all':
        societies = tag.societies.all()
    if resource_type == 'conferences' or resource_type == 'all':
        conferences = Resource.objects.getForNode(tag, resourceType=ResourceType.CONFERENCE)
        if template_name in ('tag_landing.html', 'tag_landing_mobile.html'):

            for conference in conferences:
                if len(conference.url.strip()) and  not re.compile('^https?://').match(conference.url):
                    conference.url = 'http://' + conference.url
                
            # Sort the conferences by year latest to earliest.
            conferences = list(sorted(conferences, key=lambda resource: resource.year, reverse=True))
            conferences = util.group_conferences_by_series(conferences)
            conf_count = len(conferences)
        else:
            conf_count = conferences.count()
    if resource_type == 'periodicals' or resource_type == 'all':
        periodicals = Resource.objects.getForNode(tag, resourceType=ResourceType.PERIODICAL)
    if resource_type == 'standards' or resource_type == 'all':
        standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    if resource_type == 'xplore_edu' or resource_type == 'all':
        xplore_edu_results, xplore_edu_error, totaledufound = _get_xplore_results(tag.name, False, ctype='Educational Courses')
    if resource_type == 'xplore' or resource_type == 'all':
        xplore_results, xplore_error, totalfound = _get_xplore_results(tag.name, False)
    
    page_date = datetime.datetime.now()
    
    related_items_count = sectors.count() + related_tags.count() + societies.count() + conf_count + periodicals.count() + standards.count() + totaledufound+ totalfound
    
    if resource_type == 'jobs' or resource_type == 'all':
        jobsUrl = "http://jobs.ieee.org/jobs/search/results?%s&rows=25&format=json" % urllib.urlencode({"kwsMustContain": tag.name})
        file1 = urllib2.urlopen(jobsUrl).read()
        jobsJson = json.loads(file1)
        jobsCount = jobsJson.get('Total')
        jobs = jobsJson.get('Jobs')
        for job in jobs:
            jobsHtml = jobsHtml + '<a href="%(Url)s" target="_blank" class="featured"><b>%(JobTitle)s</b></a> %(Company)s<br>\n' % job

        file1 = None

    try:
        xplore_article = _get_xplore_results(tag.name, show_all=False, offset=0, sort=XPLORE_SORT_PUBLICATION_YEAR, sort_desc=True)[0][0]
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
        'toc': toc,
        'create_links': create_links,
        'related_items_count': related_items_count,
        'jobsHtml': jobsHtml,
        'close_conference': tag._get_closest_conference(),
        'definition': tag._get_definition_link(),
        'xplore_article': xplore_article,
        'overview': overview  
    })

def debug_error(request):
    'DEBUG: Causes an error, to test the error handling.'
    test = 0/0

@login_required
def debug_send_email(request):
    'DEBUG: Tests sending an email.'
    
    assert request.user.is_superuser, 'Page disabled for non superusers.'
    
    log('sending email to "%s"' % request.user.email)
    subject = 'debug_send_email() to "%s"' % request.user.email
    message = 'debug_send_email() to "%s"' % request.user.email
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.user.email], fail_silently=False)
    log('email sent.')
    return HttpResponse('Email sent to "%s"' % request.user.email)

def test_error(request):
    'DEBUG: Tests causing an error.'
    assert settings.DEBUG
    # Divide by zero error
    1/0
    return render(request, 'test_error.html')
    
def test_lightbox_error(request):
    'DEBUG: Tests a lightbox error.'
    assert settings.DEBUG
    return render(request, 'test_lightbox_error.html')
    
def test_browsers(request):
    'DEBUG: Tests a browsers error.'
    assert settings.DEBUG
    return render(request, 'test_browsers.html')
