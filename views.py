import cgi
import datetime
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

from ieeetags.models import single_row, Filter, Node, NodeType, Profile, Resource, ResourceType, Society
from ieeetags.forms import *
#from profiler import Profiler
import settings
import util
from widgets import make_display_only

TOOLTIP_MAX_CHARS = 125

def render(request, template, dictionary=None):
    "Use this instead of 'render_to_response' to enable custom context processors, which add things like MEDIA_URL to the page automatically."
    return render_to_response(template, dictionary=dictionary, context_instance=RequestContext(request))

def truncate_link_list(items, output_func, plain_output_func, max_chars, tag=None, tab_name=None):
    """
    Takes a list of items and outputs links.  If the list is > max_chars, the list is truncated with '...(10 more)' appended.
    @param items: the list of items
    @param output_func: the HTML output formatting function, takes one item as its argument
    @param output_func: the Plaintext output formatting function, takes one item as its argument.  This is used to determine the content length (w/o HTML markup tags)
    @param max_chars: the maximum length of the output, not including the '... (X more)' if necessary
    """
    items_str = ''
    items_plaintext = ''
    
    for i in range(len(items)):
        item = items[i]
        if items_str != '':
            items_plaintext += ', '
            
        str1 = output_func(item)
        #'<a href="%s">%s</a>' % (reverse('textui') + '?nodeId=%s' % item.id, item.name)
        items_plaintext += plain_output_func(item)
        
        #log('items_plaintext: %s' % items_plaintext)
        #log('len(items_plaintext): %s' % len(items_plaintext))
        
        if len(items_plaintext) > max_chars:
            # check if tab_name exists as to not mess up clusters
            if tab_name is None:
                items_str += ' ... (%s more)' % (len(items) - i)
            else:
                if tag is not None:
                    items_str += ' ... <a href="javascript:Tags.selectTag(%s, &quot;%s&quot;);">(%s more)</a>' % (tag.id, tab_name, len(items) - i)
                else:
                    items_str += ' ... (%s more)' % (len(items) - i)
            break
        else:
            if items_str != '':
                items_str += ', '
            items_str += str1
    
    return items_str

def get_min_max(list, attr):
    '''
    Finds the min and max value of the attr attribute of each item in the list.
    @param list: the list of items.
    @param attr: the name of the attribute to check the value.
    @return: A 2-tuple (min, max).
    '''
    min1 = None
    max1 = None
    for item in list:
        if min1 is None or getattr(item, attr) < min1:
            min1 = getattr(item, attr)
        if max1 is None or getattr(item, attr) > max1:
            max1 = getattr(item, attr)
    return (min1, max1)
    
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
    results, errors, total_results = _get_xplore_results(tag, show_all=True)
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
            if cluster.get_sector() == sector:
                clusters.append(cluster)
        
        parent_nodes.append({
            'sector': sector,
            'clusters': clusters,
        })
    
    num_resources = Resource.objects.getForNode(tag).count()
    conferences = Resource.objects.getForNode(tag, resourceType=ResourceType.CONFERENCE)
    experts = Resource.objects.getForNode(tag, resourceType=ResourceType.EXPERT)
    periodicals = Resource.objects.getForNode(tag, resourceType=ResourceType.PERIODICAL)
    standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    
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
        + periodicals.count() \
        + standards.count() \
    
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

def _get_xplore_results(tag, highlight_search_term=True, show_all=False, offset=0):
    '''
    Get xplore results for the given tag from the IEEE Xplore search gateway.  Searches all fields for the tag phrase, returns results.
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
        'ti': tag.name,
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
                title = re.sub('(?i)(%s)' % tag.name, r'<strong>\1</strong>', title)
            
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
    tagId = request.POST['tag_id']
    tag = Node.objects.get(id=tagId)
    
    show_all = (request.POST['show_all'] == 'true')
    offset = int(request.POST.get('offset', 0))
    
    xplore_results, xplore_error, totalfound = _get_xplore_results(tag, show_all=show_all, offset=offset)
    
    return render(request, 'include_xplore_results.html', {
        'tag':tag,
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
def ajax_textui_nodes(request):
    '''
    Gets an AJAX list of tag/cluster info for the textui page.
    @param sector_id: (Optional) The sector to filter results.
    @param society_id: (Optional) The society to filter results.
    @param search_for: (Optional) A search phrase to filter results.
    @param sort: The sort method.
    @return: The HTML content for all results.
    '''
    #log('ajax_textui_nodes()')
    
    #from profiler import Profiler
    #p = Profiler('ajax_textui_nodes')
    
    sector_id = request.GET.get('sector_id', None)
    society_id = request.GET.get('society_id', None)
    search_for = request.GET.get('search_for', None)
    
    #log('  sector_id: %s' % sector_id)
    #log('  society_id: %s' % society_id)
    #log('  search_for: %s' % search_for)
    
    if sector_id == 'null':
        sector_id = None
    if society_id == 'null':
        society_id = None
    if search_for == 'null' or search_for == '':
        search_for = None
    
    #assert society_id is not None or sector_id is not None, 'Either society_id or sector_id is required'
    #assert society_id is None or sector_id is None, 'Cannot specify both society_id or sector_id'
    
    assert sector_id is None or society_id is None, 'Cannot specify both sector_id and society_id'
    
    sort = request.GET.get('sort')
    ##log('  sort: %s' % sort)
    #filterValues = request.GET.get('filterValues')
    ##log('filterValues: %s' % filterValues)
    
    if sector_id is not None and sector_id != "all":
        sector = Node.objects.get(id=sector_id)
    else:
        sector = None
    
    if society_id is not None and society_id != "all":
        society = Society.objects.get(id=society_id)
    else:
        society = None
    
    order_by = None
    extra_order_by = None
    search_page_title = None
    
    if sort is None or sort == 'alphabetical':
        order_by = 'name'
    elif sort == 'frequency':
        order_by = '-num_resources1'
    elif sort == 'num_sectors':
        extra_order_by = ['-num_sectors1']
    elif sort == 'num_related_tags':
        extra_order_by = ['-num_related_tags1']
    elif sort == 'clusters_first_alpha':
        # See below
        pass
    elif sort == 'connectedness':
        # See below
        pass
    elif sort == 'num_societies':
        extra_order_by = ['num_societies1']
    else:
        raise Exception('Unrecognized sort "%s"' % sort)
    
    #p.tick('filters')
    
    # TODO: Filters disabled for now
    #filterIds = []
    #if filterValues != '' and filterValues is not None:
    #    for filterValue in filterValues.split(','):
    #        filterIds.append(Filter.objects.getFromValue(filterValue).id)
    # TODO: Just select all filters for now
    filterIds = [filter.id for filter in Filter.objects.all()]
    
    #p.tick('Getting child_nodes')
    
    search_for_too_short = False
    
    if search_for is not None:
        # Search for nodes with a phrase
        # NOTE: <= 2 char searches take a long time (2-3 seconds), vs 200ms average for anything longer
        
        #p.tick('Searching for phrase...')
        
        # Require >= 3 chars for general search, or >= 2 chars for in-sector/in-society search.
        if len(search_for) >= 3 or (len(search_for) >= 2 and (sector_id is not None or society_id is not None)):
            
            search_words = re.split(r'\s', search_for)
            #print 'search_words: %s' % search_words
            
            from django.db.models import Q
            
            queries = None
            or_flag = False
            for word in search_words:
                ##log('  word: %r' % word)
                if word == 'OR':
                    or_flag = True
                    continue
                
                if queries is None:
                    queries = Q(name__icontains=word)
                else:
                    if or_flag:
                        queries |= Q(name__icontains=word)
                        or_flag = False
                    else:
                        queries &= Q(name__icontains=word)
            
            if sector_id is not None and sector_id != "all":
                # Search within the sector
                queries &= Q(parents__id=sector_id)
            
            elif society_id is not None and society_id != "all":
                # Search within the society
                queries &= Q(societies__id=society_id)
            
            child_nodes = Node.objects.filter(queries, node_type__name=NodeType.TAG)
            child_nodes = Node.objects.get_extra_info(child_nodes, None, filterIds)
            ##log('  child_nodes: %r' % child_nodes)
            ##log('  child_nodes.count(): %r' % child_nodes.count())
            
        else:
            # Search phrase was too short, return empty results.
            #search_page_title = 'Hi there'
            child_nodes = Node.objects.none()
            search_for_too_short = True
        
        #p.tick('Done searching for phrase.')
        
        #print 'searching for phrase "%s"' % search_for
        #print 'child_nodes: %s' % child_nodes
        
        # Get the min/max scores for these search results
        min_score = None
        max_score = None
        for node in child_nodes:
            if min_score is None:
                min_score = node.score1
            else:
                min_score = min(min_score, node.score1)
            if max_score is None:
                max_score = node.score1
            else:
                max_score = max(max_score, node.score1)
                
    elif sector_id is not None and sector_id != "all":
        # Get a sector or cluster's child nodes
        node = Node.objects.get(id=sector_id)
        society = None
        assert node.node_type.name in [NodeType.SECTOR, NodeType.TAG_CLUSTER], 'Node "%s" must be a sector or cluster' % node.name

        if node.node_type.name == NodeType.SECTOR:
            ##log('Calling child_nodes.get_extra_info() with filter ids')
            child_nodes = node.get_tags_and_clusters()
            
            # The 'filteIds' allows us to get the selected filter count via the DB (much faster)
            if len(filterIds) > 0:
                child_nodes = Node.objects.get_extra_info(child_nodes, extra_order_by, filterIds)
            else:
                child_nodes = Node.objects.get_extra_info(child_nodes, extra_order_by, None)
            
        elif node.node_type.name == NodeType.TAG_CLUSTER:
            child_nodes = Node.objects.get_extra_info(node.get_tags(), extra_order_by, filterIds)
        
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = Node.objects.get_sector_ranges(node)
        (min_score, max_score) = Node.objects.get_combined_sector_ranges(node)

    elif society_id is not None and society_id != "all":
        # Get a society's nodes
        node = None
        society = Society.objects.get(id=society_id)
        child_nodes = Node.objects.get_extra_info(society.tags, extra_order_by, filterIds)
        
        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = society.get_tag_ranges()
        (min_score, max_score) = society.get_combined_ranges()
        
    else:
        node = None
        society = None
        child_nodes = Node.objects.get_extra_info(Node.objects.filter(node_type=NodeType.objects.getFromName('tag')), extra_order_by, filterIds)
        min_score = 0
        max_score = 10000
        #assert False
    
    # Get child tags & clusters
    #p.tick('Got child tags')
    
    if sort == 'clusters_first_alpha':
        # Order clusters first, then tags; both sorted alphabetically
        #print 'sorting by clusters, then alpha'
        child_nodes = child_nodes.order_by('-node_type__name', 'name')
    elif order_by is not None:
        # Sort by one of the non-extra columns
        #print 'sorting by a normal column "%s"' % order_by
        child_nodes = child_nodes.order_by(order_by)
    
    #p.tick('Done sorting')
    
    # This saves time when we check child_node.node_type later on (prevents DB hit for every single child_node)
    child_nodes = child_nodes.select_related('node_type')
    #p.tick('done .select_related()')
    
    if sort == 'connectedness':
        # Sort by the combined score
        #print 'sorting by connectedness'
        assert settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS, 'settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS is not enabled.'
        child_nodes = Node.objects.sort_queryset_by_score(child_nodes, False)
    #p.tick('done sorting for connectedness')
    
    
    #p.tick('done converting child_nodes to list')
    #print 'before loop'
    #print 'len(child_nodes): %s' % len(child_nodes)
    
    #p.start_loop()
    child_nodes2 = []
    for child_node in child_nodes:
        #p.tick('start')
        
        filter_child_node = False
        
        ##log('child_node.name: %s' % child_node.name)
        ##log('  max_score: %s' % max_score)
        ##log('  min_score: %s' % min_score)
        
        # TODO: This is too slow, reenable later
        #num_related_tags = child_node.get_filtered_related_tag_count()
        num_related_tags = child_node.num_related_tags1
        
        #p.tick('before levels')
        
        if not settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
            # Old-style popularity colors with main color & two color blocks
            resourceLevel = _get_popularity_level(min_resources, max_resources, child_node.num_resources1)
            sectorLevel = _get_popularity_level(min_sectors, max_sectors, child_node.num_sectors1)
            related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)
        else:
            # New-style popularity colors - single color only
            combinedLevel = _get_popularity_level(min_score, max_score, child_node.score1)
                
        #p.tick('middle')
        
        if child_node.node_type.name == NodeType.TAG:
            
            #p.tick('before filter ')
            if child_node.num_selected_filters1 > 0 and child_node.num_societies1 > 0 and child_node.num_resources1 > 0:
                
                #p.tick('in filter loop')
                
                if not settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
                    # Separated color blocks
                    child_node.level = resourceLevel
                    child_node.sectorLevel = sectorLevel
                    child_node.relatedTagLevel = related_tag_level
                    child_node.num_related_tags = num_related_tags
                else:
                    # Combined scores
                    child_node.score = child_node.score1
                    child_node.level = combinedLevel
                    #child_node.min_score = min_score
                    #child_node.max_score = max_score
                
            else:
                #print 'removing node %s' % child_node.name
                #print '  child_node.num_selected_filters1: %s' % child_node.num_selected_filters1
                #print '  child_node.num_societies1: %s' % child_node.num_societies1
                #print '  child_node.num_resources1: %s' % child_node.num_resources1
                filter_child_node = True
                
            #p.tick('after filter')
                
        elif child_node.node_type.name == NodeType.TAG_CLUSTER:
            #p.tick('cluster')
            # Only show clusters that have one of the selected filters
            if child_node.filters.filter(id__in=filterIds).count():
                cluster_child_tags = child_node.get_tags()
                cluster_child_tags = Node.objects.get_extra_info(cluster_child_tags)
                
                # Find out how many of this cluster's child tags would show with the current filters
                num_child_tags = 0
                for cluster_child_tag in cluster_child_tags:
                    if cluster_child_tag.num_resources1 > 0 and cluster_child_tag.num_societies1 > 0 and cluster_child_tag.num_filters1 > 0 and cluster_child_tag.filters.filter(id__in=filterIds).count() > 0:
                        num_child_tags += 1
                
                if num_child_tags > 0:
                    # do nothing
                    pass
                else:
                    filter_child_node = True
                
        else:
            raise Exception('Unknown child node type "%s" for node "%s"' % (child_node.node_type.name, child_node.name))
        

        if not filter_child_node:
            child_nodes2.append(child_node)

        #p.tick('end')
    #p.end_loop()
    
    #p.tick('end loop')
    
    child_nodes = child_nodes2
    
    if search_for is not None:
        final_punc =  ('.', ':')[len(child_nodes) > 0]
        if sector_id is not None and sector_id != "all":
            search_page_title = '%s results for "%s" in the %s sector%s' % (len(child_nodes), search_for, sector.name, final_punc)
        elif society_id is not None and society_id != "all":
            search_page_title = '%s results for "%s" for the %s society%s' % (len(child_nodes), search_for, society.name, final_punc)
        
    
    #print 'after loop'
    #print 'len(child_nodes): %s' % len(child_nodes)
    
    #p.tick('after json')
    #p.tick('Rendering html...')
    ##log('~ajax_textui_nodes()')
    
    return render(request, 'ajax_textui_nodes.html', {
        'child_nodes': child_nodes,
        'parent_id': sector_id,
        'society_id': society_id,
        'search_for': search_for,
        'search_for_too_short': search_for_too_short,
        'search_page_title': search_page_title,
    })
    

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
        if cluster.get_sector() not in exclude_sectors:
            exclude_sectors.append(cluster.get_sector())
    
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
        
        if node1.node_type.name == NodeType.TAG_CLUSTER:
            # For a cluster, show the short name "Cluster" if we're viewing the cluster or its parent.  Otherwise, show the full name "Cluster (Sector)".
            if node.id != node1.id and node.id != node1.get_sector().id:
                label = node1.get_full_cluster_name()
            else:
                label = node1.name
        else:
            # None-cluster
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
def tooltip(request, tag_id):
    'Returns the AJAX content for the tag tooltip/flyover in textui.'
    #print 'tooltip()'
    #p = Profiler('tooltip')
    #import ipdb; ipdb.set_trace()
    parent_id = request.GET.get('parent_id', None)
    society_id = request.GET.get('society_id', None)
    search_for = request.GET.get('search_for', None)
    
    if parent_id == 'null' or parent_id == 'all':
        parent_id = None
    else:
        parent_id = int(parent_id)
    
    if society_id == 'null' or society_id == 'all':
        society_id = None
    else:
        society_id = int(society_id)
    
    #assert parent_id is not None or society_id is not None, 'Must specify either parent_id or society_id.'
    #assert parent_id is None or society_id is None, 'Cannot specify both parent_id or society_id.'
    
    #print 'parent_id: %r' % parent_id
    #print 'society_id: %r' % society_id
    #print 'search_for: %r' % search_for
    
    #log('tooltip()')
    
    node = Node.objects.filter(id=tag_id)
    node = Node.objects.get_extra_info(node)
    node = single_row(node)
    
    if node.node_type.name == NodeType.TAG:
        
        tag = node
        
        if parent_id is not None:
            parent = Node.objects.get(id=parent_id)
            #p.tick('Getting max resources')
            (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = Node.objects.get_sector_ranges(parent)
            (min_score, max_score) = Node.objects.get_combined_sector_ranges(parent)
        
        elif society_id is not None:
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
            min_score, max_score = get_min_max(child_nodes, 'score1')
            min_resources, max_resources = get_min_max(child_nodes, 'num_resources1')
            min_sectors, max_sectors = get_min_max(child_nodes, 'num_sectors1')
            min_related_tags, max_related_tags = get_min_max(child_nodes, 'num_related_tags1')
            min_societies, max_societies = get_min_max(child_nodes, 'num_societies1')
            
        else:
            assert False
        
        num_related_tags = tag.get_filtered_related_tag_count()
        num_societies = tag.societies.all()
        
        #p.tick('Getting levels')
        
        resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources1)
        sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.num_sectors1)
        related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)
        society_level = _get_popularity_level(min_societies, max_societies, tag.num_societies1)
        
        if settings.ENABLE_TEXTUI_SIMPLIFIED_COLORS:
            # New-style popularity colors - single color only
            #p.tick('simplified ui max scores')
            tagLevel = _get_popularity_level(min_score, max_score, node.score1)
        else:
            tagLevel = resourceLevel
        
        #p.tick('sector list')
        sectors_str = truncate_link_list(
            tag.get_sectors(),
            lambda item: '<a href="javascript:Tags.selectSector(%s);">%s</a>' % (item.id, item.name),
            lambda item: '%s' % item.name,
            TOOLTIP_MAX_CHARS,
            tag,
            'sector-tab'
        )
        
        #p.tick('related tag list')
        related_tags_str = truncate_link_list(
            tag.related_tags.all(),
            lambda item: '<a href="javascript:Tags.selectTag(%s);">%s</a>' % (item.id, item.name),
            lambda item: '%s' % item.name,
            TOOLTIP_MAX_CHARS,
            tag,
            'related-tab'
        )
        
        #p.tick('filtering out related tags')
        # Filter out related tags without filters (to match roamer)
        related_tags = []
        for related_tag in tag.related_tags.all():
            if related_tag.filters.count() > 0 and related_tag.resources.count() > 0:
                related_tags.append(related_tag)
                
        #p.tick('sector list')
        societies_str = truncate_link_list(
            tag.societies.all(),
            lambda item: '<a href="javascript:Tags.selectSociety(%s);">%s</a>' % (item.id, item.name),
            lambda item: '%s' % item.name,
            TOOLTIP_MAX_CHARS,
            tag,
            'society-tab'
        )
        
        show_edit_link = request.user.is_authenticated() and request.user.get_profile().role in (Profile.ROLE_SOCIETY_MANAGER, Profile.ROLE_ADMIN)
        
        #p.tick('render')
        #print '~tooltip()'
        return render(request, 'tooltip.html', {
            'tag': tag,
            'related_tags': related_tags,
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
        
        tags_str = truncate_link_list(
            cluster.get_tags(),
            #lambda item: '<a href="javascript:Tags.selectTag(%s);">%s</a>' % (item.id, item.name),
            lambda item: '%s' % item.name,
            lambda item: '%s' % item.name,
            TOOLTIP_MAX_CHARS
        )
        
        #print '~tooltip()'
        return render(request, 'tooltip_cluster.html', {
            'cluster': cluster,
            'tags': tags_str,
        })
        
    else:
        raise Exception('Unknown node type "%s" for node "%s"' % (node.node_type.name, node.name))

def ajax_video(request):
    'Returns the HTML content for the flash video.'
    return render(request, 'ajax_video.html')
    
def tag_landing(request, tag_id):
    '''
    Displays a wikipedia-style "flat" view of the resource. No tabs or other fancy UI.
    Simple uses the print_resource view passing in a different template name.
    '''
    
    return print_resource(request, tag_id, 'all', template_name='tag_landing.html', create_links=True, toc=True)

def print_resource(request, tag_id, resource_type, template_name='print_resource.html', create_links=False, toc=False):
    '''
    The print resource page.
    
    @param tag_id: The tag to print results for.
    @param resource_type: Which resource(s) to include.
    '''
    
    tag = Node.objects.get(id=tag_id)
    
    sectors = None
    related_tags = None
    societies = None
    conferences = None
    periodicals = None
    standards = None
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
    if resource_type == 'periodicals' or resource_type == 'all':
        periodicals = Resource.objects.getForNode(tag, resourceType=ResourceType.PERIODICAL)
    if resource_type == 'standards' or resource_type == 'all':
        standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    if resource_type == 'xplore' or resource_type == 'all':
        xplore_results, xplore_error, totalfound = _get_xplore_results(tag, False)
    
    page_date = datetime.datetime.now()
    
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
   
