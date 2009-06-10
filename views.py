from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect  
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from xml.dom import minidom
import logging
import os.path
import string
import sys
import traceback
from urllib import quote

from ieeetags.models import single_row, Filter, Node, NodeType, Resource, ResourceType, Society
from ieeetags.forms import *
import settings
import util

def render(request, template, dictionary=None):
    "Use this instead of 'render_to_response' to enable custom context processors, which add things like MEDIA_URL to the page automatically."
    return render_to_response(template, dictionary=dictionary, context_instance=RequestContext(request))

def protect_frontend(func):
    "Used as a decorator.  If settings.DEBUG_REQUIRE_LOGIN_FRONTEND is true, requires a login for the given request."
    
    #if settings.DEBUG_DISABLE_FRONTEND:
    #    raise Exception('This page has been disabled, please check that the URL you used is correct URL.')
    if settings.DEBUG_REQUIRE_LOGIN_FRONTEND:
        return login_required(func)
    else:
        return func

def disable_frontend():
    if settings.DEBUG_DISABLE_FRONTEND:
        #raise Exception('This page has been disabled, please check that the URL you used is correct URL.')
        raise util.EndUserException('Page Disabled', 'This page has been disabled, please check that the URL you used is correct URL.')

# ------------------------------------------------------------------------------

def error_view(request):
    "Custom error view for production servers."
    
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

@protect_frontend
def index(request):
    if settings.DEBUG_DISABLE_FRONTEND:
        return HttpResponseRedirect(reverse('admin_home'))
    
    return render(request, 'index.html')

@protect_frontend
def roamer(request):
    disable_frontend()
    
    nodeId = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId':nodeId,
        'sectors':sectors,
        'filters':filters,
    })

@protect_frontend
def textui(request):
    disable_frontend()
    
    sectorId = request.GET.get('nodeId', Node.objects.getFirstSector().id)
    node = Node.objects.get(id=sectorId)
    
    # Double check to make sure we didn't get a root or tag node
    if node.node_type.name == 'root':
        sectorId = Node.objects.getFirstSector().id
    elif node.node_type.name == 'tag':
        # NOTE: For now, use the tag's first parent sector
        sectorId = node.get_sectors()[0].id
    
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    
    return render(request, 'textui.html', {
        'sectorId':sectorId,
        'sectors':sectors,
        'filters':filters,
    })

@protect_frontend
def feedback(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            initial = {
                'email': request.user.email,
            }
        else:
            initial = {}
        form = FeedbackForm(initial=initial)
        return render(request, 'feedback.html', {
            'form': form,
        })
    else:
        form = FeedbackForm(request.POST)
        if form.is_valid():
            
            # Send email
            from django.core.mail import send_mail
            import time
            
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
    return render(request, 'browser_warning.html')

@protect_frontend
def ajax_tag_content(request):
    disable_frontend()
    
    tagId = request.GET['tagId']
    tag = Node.objects.get(id=tagId)
    
    # Build list of icon & no-icon societies
    societies = tag.societies.all()
    iconSocieties = []
    noIconSocieties = []
    for society in societies:
        iconPath = os.path.join(settings.MEDIA_ROOT, 'images', 'sc_logos', society.abbreviation + '.jpg')
        if os.path.exists(iconPath):
            iconSocieties.append(society)
        else:
            noIconSocieties.append(society)
    
    num_resources = Resource.objects.getForNode(tag).count()
    
    conferences = Resource.objects.getForNode(tag, resourceType=ResourceType.CONFERENCE)
    experts = Resource.objects.getForNode(tag, resourceType=ResourceType.EXPERT)
    periodicals = Resource.objects.getForNode(tag, resourceType=ResourceType.PERIODICAL)
    standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    
    return render(request, 'content.html', {
        'tag':tag,
        'iconSocieties': iconSocieties,
        'noIconSocieties': noIconSocieties,
        'num_societies': societies.count(),
        'conferences': conferences,
        'experts': experts,
        'periodicals': periodicals,
        'standards': standards,
        'num_resources': num_resources,
    })

@protect_frontend
def ajax_node(request):
    "Returns JSON data for the given node, including its parents."
    disable_frontend()
    
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
    
    json = simplejson.dumps(data, sort_keys=True, indent=4)
    
    return HttpResponse(json, mimetype="application/json")


_POPULARITY_LEVELS = [
    'level1',
    'level2',
    'level3',
    'level4',
    'level5',
    'level6',
]

def _get_popularity_level(min, max, count):
    if min == max:
        return _POPULARITY_LEVELS[len(_POPULARITY_LEVELS)-1]
    level = int(round((count-min) / float(max-min) * float(len(_POPULARITY_LEVELS)-1))) + 1
    return 'level' + str(level)

@protect_frontend
def ajax_nodes_json(request):
    disable_frontend()
    
    sectorId = request.GET['sectorId']
    sort = request.GET.get('sort')
    filterValues = request.GET.get('filterValues')
    
    if sort is None or sort == 'alphabetical':
        orderBy = 'name'
    elif sort == 'frequency':
        orderBy = 'num_resources'
    elif sort == 'num_sectors':
        orderBy = None
    elif sort == 'num_related_tags':
        orderBy = None
    else:
        raise Exception('Unrecognized sort "%s"' % sort)
    
    filterIds = []
    if filterValues != '':
        for filterValue in filterValues.split(','):
            filterIds.append(Filter.objects.getFromValue(filterValue).id)
            
    # Build node list
    sector = Node.objects.get(id=sectorId)
    if sort == 'num_sectors':
        # TODO: Handle clusters here
        tags = sector.child_nodes.extra(
            select={ 'num_parents': 'SELECT COUNT(*) FROM ieeetags_node_parents WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id' },
            order_by=['-num_parents', 'name'],
        )        
        
    elif sort == 'num_related_tags':
        # TODO: Handle clusters here
        tags = sector.child_nodes.extra(
            select={ 'num_related_tags': 'SELECT COUNT(*) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id' },
            order_by=['-num_related_tags', 'name'],
        )        
        
    else:
        #tags = sector.child_nodes.order_by(orderBy)
        # Get only tags (no clusters)
        # TODO: Handle clusters here
        tags = sector.get_tags().order_by(orderBy)
    
    (minResources, maxResources) = Node.objects.get_resource_range(sector)
    (min_sectors, max_sectors) = Node.objects.get_sector_range(sector)
    (min_related_tags, max_related_tags) = Node.objects.get_related_tag_range(sector)
    
    # JSON Output
    data = []
    for tag in tags:
        #print 'tag.name: %s' % tag.name
        #print 'tag.num_resources: %s' % tag.num_resources
        #print 'tag.parents.count(): %s' % tag.parents.count()
        
        resourceLevel = _get_popularity_level(minResources, maxResources, tag.num_resources)
        sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.parents.count())
        related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, tag.related_tags.count())
        
        # Only show tags that have one of the selected filters, and also are associated with a society
        if (settings.DEBUG_TAGS_HAVE_ALL_FILTERS or len(tag.filters.filter(id__in=filterIds))) and tag.societies.count() > 0:
            data.append({
                'id': tag.id,
                'label': tag.name,
                'type': tag.node_type.name,
                'level': resourceLevel,
                'sectorLevel': sectorLevel,
                'relatedTagLevel': related_tag_level,
                'num_related_tags': tag.related_tags.count(),
            })
            
    json = simplejson.dumps(data, sort_keys=True, indent=4)
    return HttpResponse(json, mimetype='text/plain')

@protect_frontend
def ajax_nodes_xml(request):
    disable_frontend()
    
    "Creates an XML list of nodes & connections for Asterisq Constellation Roamer"
    #logging.debug('ajax_nodes_xml()')
    #logging.debug('  request:')
    
    nodeId = request.GET['nodeId']
    #logging.debug('  nodeId: ' + nodeId)
    
    #url = 'http://' + request.META['HTTP_HOST'] + request.META['PATH_INFO'] + '?' + request.META['QUERY_STRING']
    #logging.debug('  url: ' + url)
    
    # TODO: the depth param is ignored, doesn't seem to affect anything now
    
    node = Node.objects.get(id=nodeId)
    child_nodes = node.child_nodes.all()
    
    # Enable filtering out nodes w/o societies:
    if True:
        # If parent node is a sector, filter the child tags
        if node.node_type == NodeType.objects.getFromName(NodeType.SECTOR):
            # Filter out any tags that don't have any societies
            childNodes1 = []
            for child_node in child_nodes:
                if child_node.societies.count() > 0:
                    childNodes1.append(child_node)
            child_nodes = childNodes1
    
    # Build node list
    nodes = [node]
    nodes.extend(child_nodes)
    for parent in node.parents.all():
        nodes.append(parent)
    
    # Get related tags for this tag
    if node.node_type.name == NodeType.TAG:
        for related_tag in node.related_tags.all():
            nodes.append(related_tag)
    
    edges = []
    for childNode in child_nodes:
        edges.append((node.id, childNode.id))
    for parent in node.parents.all():
        edges.append((parent.id, node.id))
        
    # Edges for related tags
    if node.node_type.name == NodeType.TAG:
        for related_tag in node.related_tags.all():
            edges.append((node.id, related_tag.id))
            
    #print '  len(edges):', len(edges)

    # XML Output
    
    doc = minidom.Document()
    
    root = doc.createElement('graph_data')
    doc.appendChild(root)
    
    nodesElem = doc.createElement('nodes')
    root.appendChild(nodesElem)
    
    ROAMER_NODE_COLORS = {
        'selected': '#006599',
        'root': '#0000FF',
        'sector': '#FF0000',
        'tag': '#00FF00',
    }
    GRAPHIC_BORDER_COLOR = '#bad4f9'
    
    for node1 in nodes:
        nodeElem = doc.createElement('node')
        nodeElem.setAttribute('id', str(node1.id))
        nodeElem.setAttribute('label', node1.name)
        nodeElem.setAttribute('depth_loaded', str(2))
        
        nodeElem.setAttribute('graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
        nodeElem.setAttribute('selected_graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
        nodeElem.setAttribute('graphic_border_color', GRAPHIC_BORDER_COLOR)
        nodeElem.setAttribute('graphic_type', 'shape')
        nodeElem.setAttribute('graphic_shape', 'circle')
        
        if settings.DEBUG_TAGS_HAVE_ALL_FILTERS:
            # DEBUG: Fake that this node is in all filters
            filters = []
            for filter in Filter.objects.all():
                filters.append(filter.value)
        else:
            filters = []
            for filter in node1.filters.all():
                filters.append(filter.value)
        
        #print 'node1.name:', node1.name
        #print 'len(node1.filters.all()):', len(node1.filters.all())
        #print "string.join(filters, ','):", string.join(filters, ',')
        #print ''
        
        #nodeElem.setAttribute('filter_groups', 'emerging_technologies,foundation_technologies,hot_topics,market_areas')
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
    #    print 'XML: ----------'
    #    print doc.toprettyxml()
    #    print '---------------'
    
    #return HttpResponse(doc.toprettyxml(), 'text/plain')
    return HttpResponse(doc.toprettyxml(), 'text/xml')

@protect_frontend
def tooltip(request):
    disable_frontend()
    
    tag_id = request.GET['tag_id']
    sector_id = request.GET['sector_id']
    
    tag = Node.objects.get(id=tag_id)
    sector = single_row(tag.parents.filter(id=sector_id))

    (min_resources, max_resources) = Node.objects.get_resource_range(sector)
    (min_sectors, max_sectors) = Node.objects.get_sector_range(sector)
    (min_related_tags, max_related_tags) = Node.objects.get_related_tag_range(sector)
    
    resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources)
    sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.parents.count())
    related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, tag.related_tags.count())
    
    return render(request, 'tooltip.html', {
        'tag': tag,
        'tagLevel': resourceLevel,
        'sectorLevel': sectorLevel,
        'relatedTagLevel': related_tag_level,
    })

def debug_error(request):
    # This causes an error
    test = 0/0

def debug_send_email(request):
    logging.debug('debug_send_email()')
    if not settings.DEBUG_ENABLE_EMAIL_TEST:
        raise Exception('DEBUG_ENABLE_EMAIL_TEST is not enabled')
        
    if request.method == 'GET':
        form = DebugSendEmailForm()
    else:
        form = DebugSendEmailForm(request.POST)
        if form.is_valid():
            logging.debug('sending email to "%s"' % form.cleaned_data['email'])
            subject = 'debug_send_email() to "%s"' % form.cleaned_data['email']
            message = 'debug_send_email() to "%s"' % form.cleaned_data['email']
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [form.cleaned_data['email']])
            logging.debug('email sent.')
            return HttpResponse('Email sent to "%s"' % form.cleaned_data['email'])
        
    return render(request, 'debug_send_email.html', {
        'form': form,
    })