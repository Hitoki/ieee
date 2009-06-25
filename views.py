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
import time
import traceback
from urllib import quote

from ieeetags.models import single_row, Filter, Node, NodeType, Resource, ResourceType, Society
from ieeetags.forms import *
import settings
import util

def render(request, template, dictionary=None):
    "Use this instead of 'render_to_response' to enable custom context processors, which add things like MEDIA_URL to the page automatically."
    return render_to_response(template, dictionary=dictionary, context_instance=RequestContext(request))

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

@login_required
def index(request):
    return render(request, 'index.html')

@login_required
def roamer(request):
    
    nodeId = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId':nodeId,
        'sectors':sectors,
        'filters':filters,
    })

@login_required
def textui(request):
    
    nodeId = request.GET.get('nodeId', None)
    sectorId = None
    
    if nodeId is None:
        # Default to the first sector (instead of the help page)
        first_sector = Node.objects.getSectors()[0]
        nodeId = first_sector.id
    
    node = Node.objects.get(id=nodeId)
    # Double check to make sure we didn't get a root or tag node
    if node.node_type.name == 'root':
        sectorId = Node.objects.getFirstSector().id
    elif node.node_type.name == 'tag':
        # TODO: a node has many sectors, for now just use the first one.
        sectorId = node.get_sectors()[0].id
    elif node.node_type.name == 'sector':
        sectorId = nodeId
    
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    
    return render(request, 'textui.html', {
        'sectorId':sectorId,
        'sectors':sectors,
        'filters':filters,
    })

@login_required
def textui_help(request):
    return render(request, 'textui_help.html')

@login_required
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

@login_required
def ajax_tag_content(request):
    
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

@login_required
def ajax_nodes_json(request):
    #logging.debug('ajax_nodes_json()')
    
    sectorId = request.GET['sectorId']
    sort = request.GET.get('sort')
    filterValues = request.GET.get('filterValues')
    
    if sort is None or sort == 'alphabetical':
        orderBy = 'name'
    elif sort == 'frequency':
        orderBy = '-num_resources1'
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
    
    #tags = sector.get_tags().extra(
    #    select={ 'num_resources1': 'SELECT COUNT(*) FROM ieeetags_resource_nodes WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id' },
    #)
    
    tags = sector.get_tags()
    tags = Node.objects.get_extra_info(tags)
    
    if sort == 'num_sectors':
        # TODO: Handle clusters here
        tags = tags.extra(
            select={ 'num_parents': 'SELECT COUNT(*) FROM ieeetags_node_parents WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id' },
            order_by=['-num_parents', 'name'],
        )        
        
    elif sort == 'num_related_tags':
        # TODO: Handle clusters here
        tags = tags.extra(
            select={ 'num_related_tags1': 'SELECT COUNT(*) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id' },
            order_by=['-num_related_tags1', 'name'],
        )        
        
    else:
        #tags = sector.child_nodes.order_by(orderBy)
        # Get only tags (no clusters)
        # TODO: Handle clusters here
        tags = tags.order_by(orderBy)
        
    (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags) = Node.objects.get_sector_ranges(sector)
    
    # JSON Output
    data = []
    for tag in tags:
        #print 'tag.name: %s' % tag.name
        #print 'tag.parents.count(): %s' % tag.parents.count()
        
        resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources1)
        sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.num_parents1)
        related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, tag.num_related_tags1)
        
        # Only show tags that have one of the selected filters, and also are associated with a society
        if (len(tag.filters.filter(id__in=filterIds))) and tag.societies.count() > 0 and (not settings.DEBUG_HIDE_TAGS_WITH_NO_RESOURCES or tag.num_resources1 > 0):
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
    
    #logging.debug('~ajax_nodes_json()')
    
    return HttpResponse(json, mimetype='application/json')

@login_required
def ajax_nodes_xml(request):
    
    "Creates an XML list of nodes & connections for Asterisq Constellation Roamer"
    logging.debug('ajax_nodes_xml()')
    
    nodeId = request.GET['nodeId']
    logging.debug('  url: ' + request.get_full_path())
    
    # TODO: the depth param is ignored, doesn't seem to affect anything now
    
    node = Node.objects.select_related('filters').get(id=nodeId)
    
    # NOTE: Can't use 'filters' in select_related() since it's a many-to-many field.
    child_nodes = node.child_nodes.select_related('node_type').all()
    child_nodes = Node.objects.get_extra_info(child_nodes)
    
    # If parent node is a sector, filter the child tags
    if node.node_type == NodeType.objects.getFromName(NodeType.SECTOR):
        # Filter out any tags that don't have any societies
        childNodes1 = []
        
        for child_node in child_nodes:
            if settings.DEBUG_HIDE_TAGS_WITH_NO_RESOURCES:
                if child_node.num_societies1 > 0 and child_node.num_resources1 > 0:
                    # Hide all tags with no societies or no resources
                    childNodes1.append(child_node)
            else:
                if child_node.num_societies1 > 0:
                    # Hide all tags with no societies
                    childNodes1.append(child_node)
        child_nodes = childNodes1
    
    # Build node list
    nodes = [node]
    nodes.extend(child_nodes)
    for parent in node.parents.all():
        nodes.append(parent)
    
    # Get related tags for this tag
    related_tags = []
    if node.node_type.name == NodeType.TAG:
        for related_tag in node.related_tags.all():
            if settings.DEBUG_HIDE_TAGS_WITH_NO_RESOURCES:
                if related_tag.societies.count() > 0 and related_tag.resources.count() > 0:
                    # Hide all tags with no societies or no resources
                    related_tags.append(related_tag)
            else:
                if related_tag.societies.count() > 0:
                    # Hide all tags with no societies
                    related_tags.append(related_tag)
    nodes.extend(related_tags)
    
    edges = []
    for childNode in child_nodes:
        edges.append((node.id, childNode.id))
    for parent in node.parents.all():
        edges.append((parent.id, node.id))
        
    # Edges for related tags
    if node.node_type.name == NodeType.TAG:
        for related_tag in related_tags:
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
        
        # This takes up 40% page time
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

@login_required
def tooltip(request):
    
    tag_id = request.GET['tag_id']
    sector_id = request.GET['sector_id']
    
    tag = Node.objects.get(id=tag_id)
    sector = single_row(tag.parents.filter(id=sector_id))
    
    (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags) = Node.objects.get_sector_ranges(sector)
    
    resourceLevel = _get_popularity_level(min_resources, max_resources, tag.resources.count())
    sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.parents.count())
    related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, tag.related_tags.count())
    
    # Filter out related tags without filters (to match roamer)
    related_tags = []
    for related_tag in tag.related_tags.all():
        if related_tag.filters.count() > 0 and (not settings.DEBUG_HIDE_TAGS_WITH_NO_RESOURCES or related_tag.resources.count() > 0):
            related_tags.append(related_tag)
    
    return render(request, 'tooltip.html', {
        'tag': tag,
        'related_tags': related_tags,
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