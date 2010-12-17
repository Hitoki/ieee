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

from ieeetags.models import single_row, Filter, Node, NodeType, Profile, Resource, ResourceType, Society, ProfileLog
from ieeetags.forms import *
#from profiler import Profiler
import settings
import util
from widgets import make_display_only

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
    
    return render(request, 'textui.html', {
        'sectorId':sectorId,
        'clusterId': clusterId,
        'sectors':sectors,
        'filters':filters,
        'societies':societies,
        'ENABLE_TEXTUI_SIMPLIFIED_COLORS': settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS,
        'ENABLE_SHOW_CLUSTERS_CHECKBOX': settings.ENABLE_SHOW_CLUSTERS_CHECKBOX,
        'ENABLE_SHOW_TERMS_CHECKBOX': settings.ENABLE_SHOW_TERMS_CHECKBOX,
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
            from django.core.mail import send_mail
            
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

@login_required
def xplore_full_results(request, tag_id):
    'Returns full listing of IEEE xplore results for the given tag.'
    tag = Node.objects.get(id=tag_id)
    results, errors, total_results = _get_xplore_results(tag.name, show_all=True)
    return render(request, 'xplore_full_results.html', {
        'tag':tag,
        'xplore_error': errors,
        'xplore_results': results,
        'totalfound': total_results,
    })

@login_required
def ajax_tag_content(request, tag_id, ui=None):
    'The AJAX resource results popup.'
    if ui is None:
        ui = 'textui'
    assert ui in ['roamer', 'textui'], 'Unrecognized ui "%s"' % ui
    
    tag = Node.objects.get(id=tag_id)
    
    sectors1 = tag.get_sectors()
    clusters1 = tag.get_parent_clusters()
    
    # Build a list of sectors and clusters, grouped by sector
    parent_nodes = []
    for sector in sectors1:
        clusters = []
        for cluster in clusters1:
            if sector in cluster.parents.all():
                clusters.append(cluster)
        
        parent_nodes.append({
            'sector': sector,
            'clusters': clusters,
        })
    
    num_resources = Resource.objects.getForNode(tag).count()
    conferences = Resource.objects.getForNode(tag, resourceType=ResourceType.CONFERENCE)
    experts = Resource.objects.getForNode(tag, resourceType=ResourceType.EXPERT)
    standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    
    # Grab periodicals with is_machine_generated field.
    periodicals_resource_nodes = tag.resource_nodes.filter(resource__resource_type__name=ResourceType.PERIODICAL)
    periodicals = []
    for periodicals_resource_node in periodicals_resource_nodes:
        periodical = periodicals_resource_node.resource
        periodical.is_machine_generated = periodicals_resource_node.is_machine_generated
        periodicals.append(periodical)
        
    # Sort the conferences by year latest to earliest.
    conferences = list(sorted(conferences, key=lambda resource: resource.year, reverse=True))
    conferences = util.group_conferences_by_series(conferences)
    
    num_related_items =  \
        sectors1.count() \
        + clusters1.count() \
        + tag.societies.count() \
        + tag.related_tags.count() \
        + len(conferences) \
        + experts.count() \
        + len(periodicals) \
        + standards.count() \
        
    if tag.is_taxonomy_term and ((sectors1.count() + tag.societies.count() + len(conferences) + experts.count() + len(periodicals) + standards.count()) == 0):
        # This is a term with no resources (except Related Tags), just show the abbreviated content popup.
        return render(request, 'ajax_term_content.html', {
            'tag':tag,
            'num_related_items': num_related_items,
            'ui': ui,
        })
    else:
        # Show the normal tag content popup.
        return render(request, 'ajax_tag_content.html', {
            'tag':tag,
            'conferences': conferences,
            'experts': experts,
            'periodicals': periodicals,
            'standards': standards,
            'num_resources': num_resources,
            'num_related_items': num_related_items,
            'parent_nodes': parent_nodes,
            'ui': ui,
            #'xplore_error': xplore_error,
            #'xplore_results': xplore_results,
        })

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

def _get_xplore_results(tag_name, highlight_search_term=True, show_all=False, offset=0):
    '''
    Get xplore results for the given tag_name from the IEEE Xplore search gateway.  Searches all fields for the tag_name phrase, returns results.
    @return: a 3-tuple of (results, errors, total_results).  'errors' is a string of any errors that occurred, or None.  'total_results' is the total number of results (regardless of how many are returned in 'results'.  'results' is an array of dicts:
        [
            {
                'name': ...
                'description': ...
                'url': ...
            },
            ...
        ]
        
    '''
    
    if show_all:
        # Some arbitrarily big number...
        max_num_results = 10000
    else:
        max_num_results = 10
    
    url = 'http://xploreuat.ieee.org/gateway/ipsSearch.jsp?' + urllib.urlencode({
    #url = 'http://ieeexplore.ieee.org/gateway/ipsSearch.jsp?' + urllib.urlencode({
        # Number of results
        'hc': max_num_results,
        # Specifies the result # to start from
        'rs': offset+1,
        'md': tag_name,
    })
    
    try:
        file1 = urllib2.urlopen(url)
    except urllib2.URLError:
        xplore_error = 'Error: Could not connect to the IEEE Xplore site to download articles.'
        xplore_results = []
        totalfound = None
    else:
        xplore_error = None
        
        # Get the charset of the request and decode/re-encode the response text into UTF-8 so we can parse it
        info = file1.info()
        temp, charset = info['content-type'].split('charset=')
        xml_body = file1.read()
        file1.close()
        xml_body = xml_body.decode(charset).encode('utf-8')
        
        xml1 = xml.dom.minidom.parseString(xml_body)
        
        def getElementByTagName(node, tag_name):
            nodes = node.getElementsByTagName(tag_name)
            if len(nodes) == 0:
                return None
            elif len(nodes) == 1:
                return nodes[0]
            else:
                raise Exception('More than one element found for tag name "%s"' % tag_name)
        
        def getElementValueByTagName(node, tag_name):
            node1 = getElementByTagName(node, tag_name)
            if node1 is None:
                return None
            else:
                value = ''
                #print '  len(node1.childNodes): %r' % len(node1.childNodes)
                for child_node in node1.childNodes:
                    #print '  child_node: %r' % child_node
                    if child_node.nodeType == child_node.TEXT_NODE or child_node.nodeType == child_node.CDATA_SECTION_NODE:
                        value += child_node.nodeValue
                    
                return value
        
        totalfound = int(getElementValueByTagName(xml1.documentElement, 'totalfound'))
        
        xplore_results = []
        for document1 in xml1.documentElement.getElementsByTagName('document'):
            rank = getElementValueByTagName(document1, 'rank')
            title = getElementValueByTagName(document1, 'title')
            abstract = getElementValueByTagName(document1, 'abstract')
            pdf = getElementValueByTagName(document1, 'pdf')
            authors = getElementValueByTagName(document1, 'authors')
            pub_title = getElementValueByTagName(document1, 'pubtitle')
            pub_year = getElementValueByTagName(document1, 'py')
            
            # Escape here, since we're going to output this as |safe on the template
            title = cgi.escape(title)
            if highlight_search_term:
                title = re.sub('(?i)(%s)' % tag_name, r'<strong>\1</strong>', title)
            
            result = {
                'rank': rank,
                'name': title,
                'description': abstract,
                'url': pdf,
                'authors': authors,
                'pub_title': pub_title,
                'pub_year': pub_year,
            }
            xplore_results.append(result)
        
    return xplore_results, xplore_error, totalfound

def ajax_xplore_results(request):
    '''
    Shows the list of IEEE xplore articles for the given tag.
    @param tag_id: POST var, specifyies the tag.
    @return: HTML output of results.
    '''
    tag_id = request.POST.get('tag_id')
    #term_id = request.POST.get('term_id')
    
    if tag_id is not None and tag_id != 'undefined':
        tag = Node.objects.get(id=tag_id)
        term = None
        name = tag.name
    #elif term_id is not None and term_id != 'undefined':
    #    term = TaxonomyTerm.objects.get(id=term_id)
    #    tag = None
    #    name = term.name
    #else:
    #    assert False, 'Must specify either tag_id or term_id.'
    else:
        assert False, 'Must specify either tag_id.'
    
    show_all = (request.POST['show_all'] == 'true')
    offset = int(request.POST.get('offset', 0))
    
    xplore_results, xplore_error, totalfound = _get_xplore_results(name, show_all=show_all, offset=offset)
    
    return render(request, 'include_xplore_results.html', {
        'name': name,
        # TODO: This should use quote(), not replace()...
        'search_term': name.replace(' ', '+'),
        'xplore_error': xplore_error,
        'xplore_results': xplore_results,
        'totalfound': totalfound,
        'show_all': show_all,
    })

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


_POPULARITY_LEVELS = [
    'level1',
    'level2',
    'level3',
    'level4',
    'level5',
    'level6',
]

def _get_popularity_level(min, max, count):
    '''
    Gets the popularity level for the given count of items.
    
    For example, if we are looking at all tags for a given sector, then we find the min/max number of related tags is 1 and 10 respectively.  Then we can call this function for each tag with params (1, 10, count) where count is the number of related tags for each tag, and we'll get a popularity level for each tag.
    
    @param min: The minimum count for all other peer items.
    @param max: The maximum count for all other peer items.
    @param count: The count for this specific item.
    @return: A text label 'level1' through 'level6'.
    '''
    if min == max:
        return _POPULARITY_LEVELS[len(_POPULARITY_LEVELS)-1]
    level = int(round((count-min) / float(max-min) * float(len(_POPULARITY_LEVELS)-1))) + 1
    return 'level' + str(level)

@login_required
#@util.profiler
def ajax_textui_nodes(request):
    '''
    Returns HTML for the list of tags/clusters for the textui page.
    @param sector_id: (Optional) The sector to filter results.
    @param society_id: (Optional) The society to filter results.
    @param cluster_id: (Optional) The cluster to filter results, used to filter "search_for" results.
    @param search_for: (Optional) A search phrase to filter results.
    @param sort: The sort method.
    @param page: The current tab/page ("sector" or "society").
    @return: The HTML content for all results.
    '''
    log('ajax_textui_nodes()')
    
    sector_id = request.GET.get('sector_id', None)
    if sector_id == '' or sector_id == 'null' or sector_id == 'all':
        sector_id = None
    try:
        sector_id = int(sector_id)
        sector = Node.objects.get(id=sector_id, node_type__name=NodeType.SECTOR)
    except (TypeError, ValueError):
        sector = None
    assert sector_id is None or type(sector_id) is int, 'Bad value for sector_id %r' % sector_id
    
    society_id = request.GET.get('society_id', None)
    if society_id == '' or society_id == 'null' or society_id == 'all':
        society_id = None
    try:
        society_id = int(society_id)
        society = Society.objects.get(id=society_id)
    except (TypeError, ValueError):
        society = None
    assert society_id is None or type(society_id) is int, 'Bad value for society_id %r' % society_id
        
    cluster_id = request.GET.get('cluster_id', None)
    if cluster_id == '' or cluster_id == 'null':
        cluster_id = None
    try:
        cluster_id = int(cluster_id)
        cluster = Node.objects.get(id=cluster_id, node_type__name=NodeType.TAG_CLUSTER)
    except (TypeError, ValueError):
        cluster = None
    assert cluster_id is None or type(cluster_id) is int, 'Bad value for cluster_id %r' % cluster_id
    
    search_for = request.GET.get('search_for', None)
    if search_for == 'null' or search_for == '':
        search_for = None
    
    show_clusters = request.GET.get('show_clusters', 'false')
    assert show_clusters in ['true', 'false'], 'show_clusters (%r) was not "true" or "false".' % (show_clusters)
    show_clusters = (show_clusters == 'true')
    
    assert show_clusters or settings.ENABLE_SHOW_CLUSTERS_CHECKBOX, 'Cannot show_clusters=false if ENABLE_SHOW_CLUSTERS_CHECKBOX is not set.'
    
    show_terms = request.GET.get('show_terms', 'false')
    assert show_terms in ['true', 'false'], 'show_terms (%r) was not "true" or "false".' % (show_terms)
    show_terms = (show_terms == 'true')
    
    assert show_terms or settings.ENABLE_SHOW_TERMS_CHECKBOX, 'Cannot set show_terms=false if ENABLE_SHOW_TERMS_CHECKBOX is not set.'
    
    log('  sector_id: %s' % sector_id)
    log('  society_id: %s' % society_id)
    log('  cluster_id: %s' % cluster_id)
    log('  search_for: %s' % search_for)
    log('  show_clusters: %s' % show_clusters)
    log('  show_terms: %s' % show_terms)
    
    log('  sector: %s' % sector)
    log('  society: %s' % society)
    log('  cluster: %s' % cluster)
    
    assert sector_id is None or society_id is None, 'Cannot specify both sector_id and society_id.'
    assert show_clusters or cluster_id is None, 'Cannot specify cluster_id and show_clusters=false.'
    
    sort = request.GET.get('sort')
    log('  sort: %s' % sort)
    
    page = request.GET['page']
    log('  page: %s' % page)
    if page != 'sector' and page != 'society':
        raise Exception('page (%r) should be "sector" or "society"' % page)
    
    #filterValues = request.GET.get('filterValues')
    ##log('filterValues: %s' % filterValues)
    
    log('')
    
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
    
    #terms = []
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
                
            # Only add terms if search is:
            #   - within a cluster.
            #   - in all sectors.
            #   - in all societies.
            # Otherwise we can't show anything, since terms are not associated with societies/sectors, only clusters.
            #if show_terms and sector_id is None and society_id is None:
            #    log('  adding terms for search phrase')
            #    terms = TaxonomyTerm.objects.all()
            #    
            #    # Search for keywords.
            #    terms = terms.filter(word_queries)
            #    #log('  terms.count(): %r' % terms.count())
            #    
            #    # Filter by cluster
            #    if cluster_id is not None:
            #        cluster = Node.objects.get(id=cluster_id, node_type__name=NodeType.TAG_CLUSTER)
            #        taxonomy_cluster = TaxonomyCluster.objects.get(name=cluster.name)
            #        terms = terms.filter(taxonomy_clusters__id=taxonomy_cluster.id)
            #        #log('  terms.count(): %r' % terms.count())
            #    
            #    # Filter out any terms matched to existing tags.
            #    terms = terms.annotate(num_related_nodes=Count('related_nodes')).filter(num_related_nodes=0)
            #    #log('  terms.count(): %r' % terms.count())
                
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
        
        # Only show terms from the cluster here if we're not in a sector or society.
        #if show_terms and not word_queries and sector is None and society is None:
        #    log('  adding terms for cluster.')
        #    taxonomy_cluster = TaxonomyCluster.objects.get(name=cluster.name)
        #    terms = taxonomy_cluster.terms.all()
        #    
        #    # Filter out any terms matched to existing tags.
        #    terms = terms.annotate(num_related_nodes=Count('related_nodes')).filter(num_related_nodes=0)
    
    if show_clusters:
        # Restrict to only tags & clusters.
        child_nodes = child_nodes.filter(Q(node_type__name=NodeType.TAG) | Q(node_type__name=NodeType.TAG_CLUSTER))
    else:
        # Restrict to only tags.
        child_nodes = child_nodes.filter(node_type__name=NodeType.TAG)
    child_nodes = Node.objects.get_extra_info(child_nodes, extra_order_by, filterIds)
    
    if word_queries:
        log('  using min/max for all results.')
        # Get the min/max scores for these search results
        min_score = None
        max_score = None
        for node1 in child_nodes:
            if min_score is None:
                min_score = node1.score1
            else:
                min_score = min(min_score, node1.score1)
            if max_score is None:
                max_score = node1.score1
            else:
                max_score = max(max_score, node1.score1)
    if cluster:
        # Get min/max scores for this cluster.
        #log('  getting min/max for this cluster.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = cluster.get_sector_ranges()
        (min_score, max_score) = cluster.get_combined_sector_ranges()
    elif sector:
        # Get min/max scores for this sector.
        #log('  getting min/max for this sector.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = sector.get_sector_ranges()
        (min_score, max_score) = sector.get_combined_sector_ranges()
    elif society:
        # Get min/max scores for this society.
        #log('  getting min/max for this society.')
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = society.get_tag_ranges()
        (min_score, max_score) = society.get_combined_ranges()
    else:
        # Get min/max scores for all tags/clusters (root node).
        #log('  getting min/max for root node.')
        if sector_id is None and society_id is None:
            root_node = Node.objects.get(node_type__name=NodeType.ROOT)
            (min_score, max_score) = root_node.get_combined_sector_ranges()
        else:
            min_score = 0
            max_score = 10000
    
    #log('  min_resources: %s' % min_resources)
    #log('  max_resources: %s' % max_resources)
    #log('  min_score: %s' % min_score)
    #log('  max_score: %s' % max_score)
    
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
    
    if show_terms and (word_queries or (cluster and show_terms and not word_queries and sector is None and society is None)):
        # Show empty terms if we're:
        # 1. Searching by phrase, or
        # 2. Searching within a cluster, but not in any sector/society.
        show_empty_terms = True
    else:
        show_empty_terms = False
    
    clusters = []
    child_nodes2 = []
    for child_node in child_nodes.values(
        'id',
        'name',
        'node_type__name',
        'num_related_tags1',
        'num_resources1',
        'num_sectors1',
        'num_selected_filters1',
        'num_societies1',
        'score1',
        'is_taxonomy_term',
    ):
        filter_child_node = False
        
        # TODO: This is too slow, reenable later
        #num_related_tags = child_node['get_filtered_related_tag_count']()
        num_related_tags = child_node['num_related_tags1']
        
        if not settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
            # Old-style popularity colors with main color & two color blocks
            resourceLevel = _get_popularity_level(min_resources, max_resources, child_node['num_resources1'])
            sectorLevel = _get_popularity_level(min_sectors, max_sectors, child_node['num_sectors1'])
            related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)
        else:
            # New-style popularity colors - single color only
            combinedLevel = _get_popularity_level(min_score, max_score, child_node['score1'])
                
        
        if child_node['node_type__name'] == NodeType.TAG:
            
            # Show all terms, and all tags with content.
            if (show_empty_terms and child_node['is_taxonomy_term']) or (child_node['num_selected_filters1'] > 0 and child_node['num_societies1'] > 0 and child_node['num_resources1'] > 0):
                
                if not settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
                    # Separated color blocks
                    child_node['level'] = resourceLevel
                    child_node['sectorLevel'] = sectorLevel
                    child_node['relatedTagLevel'] = related_tag_level
                    child_node['num_related_tags'] = num_related_tags
                else:
                    # Combined scores
                    child_node['score'] = child_node['score1']
                    child_node['level'] = combinedLevel
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
            child_node['level'] = ''
            
            # Make sure clusters show on top of the list.
            filter_child_node = True
            clusters.append(child_node)
                
        else:
            raise Exception('Unknown child node type "%s" for node "%s"' % (child_node['node_type__name'], child_node['name']))
        
        if not filter_child_node:
            child_nodes2.append(child_node)
    
    # Add any matching taxonomy terms to the results.
    #terms2 = []
    #for term in terms:
    #    terms2.append({
    #        'name': term.name,
    #        'level': '',
    #        'num_related_tags1': 0,
    #        'num_sectors1': 0,
    #        'score': 0,
    #        'num_resources1': 0,
    #        'node_type__name': 'term',
    #        'num_selected_filters1': 0,
    #        'id': term.id,
    #        'num_societies1': 0,
    #        'score1': 0,
    #    })
    
    num_clusters = len(clusters)
    # TODO: Should this include terms?
    #num_tags = len(child_nodes2) + len(terms2)
    num_tags = len(child_nodes2)
    
    #child_nodes = clusters + child_nodes2 + terms2
    child_nodes = clusters + child_nodes2
    
    if search_for is not None:
        final_punc =  ('.', ':')[len(child_nodes) > 0]
        if sector_id is not None:
            str = ' in the %s node%s' % (sector.name, final_punc)
            search_page_title = {"num": len(child_nodes), "search_for": search_for, "node_desc": str}
        elif society_id is not None:
            str = ' for the %s society%s' % (society.name, final_punc)
            search_page_title = {"num": len(child_nodes), "search_for": search_for, "node_desc": str}
    
    #log('  num_clusters: %s' % num_clusters)
    #log('  num_tags: %s' % num_tags)
    #log('    # real tags: %s' % len(child_nodes2))
    #log('    # terms: %s' % len(terms2))
    
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
        'page': page,
    })
    
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
    params['search_for'] = search_for
    params['page'] = page
    
    textui_flyovers_url = reverse('tooltip') + '/tagid?' + urllib.urlencode(params)
    
    node_count_content = render_to_string('ajax_textui_node_count.inc.html', {
        'child_nodes': child_nodes,
        'num_clusters': num_clusters,
        'num_tags': num_tags,
        'search_for': search_for,
        'search_for_too_short': search_for_too_short,
        'search_page_title': search_page_title,
    })
    
    return HttpResponse(json.dumps({
        'search_for': search_for,
        'content': content,
        'node_count_content': node_count_content,
        'textui_flyovers_url': textui_flyovers_url,
    }), 'text/plain')
    
@login_required
def ajax_nodes_xml(request):
    "Creates an XML list of nodes & connections for Asterisq Constellation Roamer."
    
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
    
    # NOTE: Can't use 'filters' in select_related() since it's a many-to-many field.
    child_nodes = child_nodes.select_related('node_type').all()
    child_nodes = Node.objects.get_extra_info(child_nodes)
    
    # If parent node is a sector, filter the child tags
    if node.node_type.name == NodeType.SECTOR or node.node_type.name == NodeType.TAG_CLUSTER:
        # Filter out any tags that don't have any societies
        childNodes1 = []
        
        for child_node in child_nodes:
            # List all clusters, plus any tags that have societies and resoureces
            if child_node.node_type.name == NodeType.TAG_CLUSTER or (child_node.num_societies1 > 0 and child_node.num_resources1 > 0 and child_node.num_filters1 > 0):
                childNodes1.append(child_node)
        child_nodes = childNodes1
    
    # The main node
    nodes = [node]
    
    # First sorting by connectedness here, so we get the X most connected nodes (with the hard limit)
    if settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
        child_nodes = Node.objects.sort_queryset_by_score(child_nodes, False)
    
    # Add the node's children
    # TODO: Number of child nodes is temporarily limited to a hard limit... remove this later
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
        # ie. If 'node1' is in 'cluster1' in the 'Agriculture' sector, don't show 'Agriculture'.
        if sector not in exclude_sectors:
            nodes.append(sector)
            parent_nodes.append(sector)
    
    # Get related tags for this tag
    related_tags = []
    if node.node_type.name == NodeType.TAG:
        for related_tag in node.related_tags.all():
            if related_tag.filters.count() > 0 and related_tag.societies.count() > 0 and related_tag.resources.count() > 0:
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
        
        nodeElem.setAttribute('graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
        nodeElem.setAttribute('selected_graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
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
            raise Exception('Unknown node type "%s" for node "%s"' % (node1.node_type.name, node1.name))
        
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

@login_required
def tooltip(request, tag_id=None):
    'Returns the AJAX content for the tag tooltip/flyover in textui.'
    parent_id = request.GET.get('parent_id', None)
    society_id = request.GET.get('society_id', None)
    search_for = request.GET.get('search_for', None)
    #term_id = request.GET.get('term_id', None)
    page = request.GET.get('page', None)
    
    #if tag_id is None and term_id is None:
    #    raise Exception('Must specify either "tag_id" or "term_id".')
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
    
    print '  tag_id: %r' % tag_id
    print '  parent_id: %r' % parent_id
    print '  search_for: %r' % search_for
    print '  society_id: %r' % society_id
    #print '  term_id: %r' % term_id
    
    if tag_id is not None:
        
        node = Node.objects.filter(id=tag_id)
        node = Node.objects.get_extra_info(node)
        node = single_row(node)
        
        print '  node.node_type.name: %r' % node.node_type.name
        
        if node.node_type.name == NodeType.TAG:
            
            tag = node
            
            if node.is_taxonomy_term:
                
                # Taxonomy Term Tag
                
                tags = tag.related_tags.all()
                
                tags_str = util.truncate_link_list(
                    tags,
                    lambda item: '%s' % item.name,
                    lambda item: '%s' % item.name,
                    TOOLTIP_MAX_CHARS
                )
                
                return render(request, 'tooltip_term.html', {
                    'tag': tag,
                    'sector_id': None,
                })
            
            else:
                
                # Normal Tag
                
                if parent_id is not None:
                    if (parent_id == "all"):
                        parent = Node.objects.get(node_type=Node.objects.getNodesForType(NodeType.ROOT))
                        tags = Node.objects.get_tags()
                    else:
                        parent = Node.objects.get(id=parent_id)
                        tags = parent.child_nodes
                    tags = Node.objects.get_extra_info(tags)
                    tags = tags.values(
                        'num_filters1',
                        'num_related_tags1',
                        'num_resources1',
                        'num_sectors1',
                        'num_societies1',
                        'score1',
                    )
                    (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = parent.get_sector_ranges(tags)
                    (min_score, max_score) = parent.get_combined_sector_ranges(tags)
                
                elif society_id is not None:
                    if society_id == 'all':
                        # For All Societies, check all tags to get mins/maxes.
                        from django.db.models import Count, Min, Max
                        tags = Node.objects.get_tags()
                        tags = Node.objects.get_extra_info(tags)
                        
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
                        for tag1 in tags.values(
                            'num_resources1',
                            'num_sectors1',
                            'num_related_tags1',
                            'num_societies1',
                            'score1',
                        ):
                            if min_resources is None or tag1['num_resources1'] < min_resources:
                                min_resources = tag1['num_resources1']
                            if max_resources is None or tag1['num_resources1'] < max_resources:
                                max_resources = tag1['num_resources1']
                            if min_sectors is None or tag1['num_sectors1'] < min_sectors:
                                min_sectors = tag1['num_sectors1']
                            if max_sectors is None or tag1['num_sectors1'] < max_sectors:
                                max_sectors = tag1['num_sectors1']
                            if min_related_tags is None or tag1['num_related_tags1'] < min_related_tags:
                                min_related_tags = tag1['num_related_tags1']
                            if max_related_tags is None or tag1['num_related_tags1'] < max_related_tags:
                                max_related_tags = tag1['num_related_tags1']
                            if min_societies is None or tag1['num_societies1'] < min_societies:
                                min_societies = tag1['num_societies1']
                            if max_societies is None or tag1['num_societies1'] < max_societies:
                                max_societies = tag1['num_societies1']
                            if min_score is None or tag1['score1'] < min_score:
                                min_score = tag1['score1']
                            if max_score is None or tag1['score1'] < max_score:
                                max_score = tag1['score1']
                    else:
                        society = Society.objects.get(id=society_id)
                        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = society.get_tag_ranges()
                        (min_score, max_score) = society.get_combined_ranges()
                    
                elif search_for is not None:
                    # Search for nodes with a phrase
                    if len(search_for) >= 2:
                        search_words = re.split(r'\s', search_for)
                        from django.db.models import Q
                        queries = None
                        for word in search_words:
                            if queries is None:
                                queries = Q(name__icontains=word)
                            else:
                                queries &= Q(name__icontains=word)
                        #child_nodes = Node.objects.filter(name__icontains=search_for, node_type__name=NodeType.TAG)
                        child_nodes = Node.objects.filter(queries, node_type__name=NodeType.TAG)
                        filterIds = [filter.id for filter in Filter.objects.all()]
                        child_nodes = Node.objects.get_extra_info(child_nodes, None, filterIds)
                    else:
                        child_nodes = Node.objects.none()
                    
                    # Get the min/max for these search results
                    # TODO: These don't account for filter==0, num_resources1==0, etc.
                    min_score, max_score = util.get_min_max(child_nodes, 'score1')
                    min_resources, max_resources = util.get_min_max(child_nodes, 'num_resources1')
                    min_sectors, max_sectors = util.get_min_max(child_nodes, 'num_sectors1')
                    min_related_tags, max_related_tags = util.get_min_max(child_nodes, 'num_related_tags1')
                    min_societies, max_societies = util.get_min_max(child_nodes, 'num_societies1')
                    
                else:
                    # No sector/society/search phrase - could be in "All Sectors" or "All Societies"
                    assert False, "TODO"
                
                num_related_tags = tag.get_filtered_related_tag_count()
                num_societies = tag.societies.all()
                
                resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources1)
                sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.num_sectors1)
                related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)
                society_level = _get_popularity_level(min_societies, max_societies, tag.num_societies1)
                
                if settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
                    # New-style popularity colors - single color only
                    tagLevel = _get_popularity_level(min_score, max_score, node.score1)
                else:
                    tagLevel = resourceLevel
                
                sectors_str = util.truncate_link_list(
                    tag.get_sectors(),
                    lambda item: '<a href="javascript:Tags.selectSector(%s);">%s</a>' % (item.id, item.name),
                    lambda item: '%s' % item.name,
                    TOOLTIP_MAX_CHARS,
                    tag,
                    'sector-tab'
                )
                
                related_tags_str = util.truncate_link_list(
                    tag.related_tags.all(),
                    lambda item: '<a href="javascript:Tags.selectTag(%s);">%s</a>' % (item.id, item.name),
                    lambda item: '%s' % item.name,
                    TOOLTIP_MAX_CHARS,
                    tag,
                    'related-tab'
                )
                
                # Filter out related tags without filters (to match roamer)
                related_tags2 = tag.related_tags.all()
                related_tags2 = Node.objects.get_extra_info(related_tags2)
                related_tags = []
                for related_tag in related_tags2:
                    if related_tag.num_filters1 > 0 and related_tag.num_resources1 > 0:
                        related_tags.append(related_tag)
                
                societies_str = util.truncate_link_list(
                    tag.societies.all(),
                    lambda item: '<a href="javascript:Tags.selectSociety(%s);">%s</a>' % (item.id, item.name),
                    lambda item: '%s' % item.name,
                    TOOLTIP_MAX_CHARS,
                    tag,
                    'society-tab'
                )
                
                show_edit_link = request.user.is_authenticated() and request.user.get_profile().role in (Profile.ROLE_SOCIETY_MANAGER, Profile.ROLE_ADMIN)
                
                return render(request, 'tooltip.html', {
                    'tag': tag,
                    'tagLevel': tagLevel,
                    'sectorLevel': sectorLevel,
                    'relatedTagLevel': related_tag_level,
                    'societyLevel' : society_level,
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
                #lambda item: '<a href="javascript:Tags.selectTag(%s);">%s</a>' % (item.id, item.name),
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
            raise Exception('Unknown node type "%s" for node "%s"' % (node.node_type.name, node.name))
    
    else:
        assert False

def ajax_video(request):
    'Returns the HTML content for the flash video.'
    return render(request, 'ajax_video.html')

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

def tags_list(request):
    '''
    Displays a list of links to the tag "wikipedia-style" pages (see views.tag_landing)
    Mostly useful for spider link discovery and SEO.
    '''
    
    return render_to_response('tags_list.html', {"tags": Node.objects.get_tags()}, context_instance=RequestContext(request));
    
def tag_landing(request, tag_id):
    '''
    Displays a wikipedia-style "flat" view of the resource. No tabs or other fancy UI.
    Simply uses the print_resource view passing in a different template name.
    '''
    return print_resource(request, tag_id, 'all', template_name='tag_landing.html', create_links=True, toc=True)

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
    periodicals = Node.objects.none()
    standards = Node.objects.none()
    conf_count = 0
    totalfound = 0
    xplore_results = None
    
    if resource_type not in ['all', 'sectors', 'related_tags', 'societies', 'conferences', 'periodicals', 'standards', 'xplore']:
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
        if template_name == 'tag_landing.html':
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
    if resource_type == 'xplore' or resource_type == 'all':
        xplore_results, xplore_error, totalfound = _get_xplore_results(tag.name, False)
    
    page_date = datetime.datetime.now()
    
    related_items_count = sectors.count() + related_tags.count() + societies.count() + conf_count + periodicals.count() + standards.count() + totalfound
        
        
    return render(request, template_name, {
        'page_date': page_date,
        'tag': tag,
        'sectors': sectors,
        'related_tags': related_tags,
        'societies': societies,
        'conferences': conferences,
        'periodicals': periodicals,
        'standards': standards,
        'xplore_results': xplore_results,
        'toc': toc,
        'create_links': create_links,
        'related_items_count': related_items_count
    })

def debug_error(request):
    'DEBUG: Causes an error, to test the error handling.'
    test = 0/0

def debug_send_email(request):
    'DEBUG: Tests sending an email.'
    if not settings.DEBUG_ENABLE_EMAIL_TEST:
        raise Exception('DEBUG_ENABLE_EMAIL_TEST is not enabled')
        
    if request.method == 'GET':
        form = DebugSendEmailForm()
    else:
        form = DebugSendEmailForm(request.POST)
        if form.is_valid():
            log('sending email to "%s"' % form.cleaned_data['email'])
            subject = 'debug_send_email() to "%s"' % form.cleaned_data['email']
            message = 'debug_send_email() to "%s"' % form.cleaned_data['email']
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [form.cleaned_data['email']])
            log('email sent.')
            return HttpResponse('Email sent to "%s"' % form.cleaned_data['email'])
        
    return render(request, 'debug_send_email.html', {
        'form': form,
    })

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
   
