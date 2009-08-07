from django.contrib.auth.decorators import login_required
from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect  
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from xml.dom import minidom
from logging import debug as log
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
from widgets import make_display_only

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

def site_disabled(request):
    return render(request, 'site_disabled.html', {
    })
    
@login_required
def index(request):
    # TODO: Temporarily show the textui page first, since roamer has performance problems.
    return HttpResponseRedirect(reverse('textui'))
    #return render(request, 'index.html')

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
    clusterId = None
    
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
    elif node.node_type.name == 'tag_cluster':
        clusterId = nodeId
    else:
        raise Exception('Unknown node_type "%s"' % node.node_type.name)
    
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    
    return render(request, 'textui.html', {
        'sectorId':sectorId,
        'clusterId': clusterId,
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
    
    return HttpResponse(json, mimetype="text/plain")


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
    log('ajax_nodes_json()')
    
    node_id = request.GET['nodeId']
    log('  node_id: %s' % node_id)
    
    sort = request.GET.get('sort')
    log('  sort: %s' % sort)
    
    filterValues = request.GET.get('filterValues')
    
    #log('filterValues: %s' % filterValues)
    
    order_by = None
    extra_order_by = None
    
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
    else:
        raise Exception('Unrecognized sort "%s"' % sort)
    
    filterIds = []
    if filterValues != '':
        for filterValue in filterValues.split(','):
            filterIds.append(Filter.objects.getFromValue(filterValue).id)
    
    node = Node.objects.get(id=node_id)
    assert node.node_type.name in [NodeType.SECTOR, NodeType.TAG_CLUSTER], 'Node "%s" must be a sector or cluster' % node.name
    
    # Get child tags & clusters
    
    if node.node_type.name == NodeType.SECTOR:
        child_nodes = Node.objects.get_extra_info(node.get_tags_and_clusters(), extra_order_by)
    elif node.node_type.name == NodeType.TAG_CLUSTER:
        child_nodes = Node.objects.get_extra_info(node.get_tags(), extra_order_by)
    else:
        raise Exception('Unrecognized node type "%s" for node "%s"' % (node.node_type.name, node.name))
    
    if sort == 'clusters_first_alpha':
        # Order clusters first, then tags; both sorted alphabetically
        child_nodes = child_nodes.order_by('-node_type__name', 'name')
    elif order_by is not None:
        # Sort by one of the non-extra columns
        child_nodes = child_nodes.order_by(order_by)
        
    (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags) = Node.objects.get_sector_ranges(node)
    
    # JSON Output
    data = {
        'node': {
            'id': node.id,
            'label': node.name,
            'type': node.node_type.name,
        },
        'child_nodes': [],
    }
    
    if node.node_type.name == NodeType.TAG_CLUSTER:
        data['node']['sector'] = {
            'id': node.get_sector().id,
            'label': node.get_sector().name,
        }
    
    for child_node in child_nodes:
        num_related_tags = child_node.get_filtered_related_tag_count()
        
        resourceLevel = _get_popularity_level(min_resources, max_resources, child_node.num_resources1)
        sectorLevel = _get_popularity_level(min_sectors, max_sectors, child_node.num_sectors1)
        related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)
        
        if child_node.node_type.name == NodeType.TAG:
            # Only show tags that have one of the selected filters, and also are associated with a society
            if (len(child_node.filters.filter(id__in=filterIds))) and child_node.societies.count() > 0 and child_node.num_resources1 > 0:
                data['child_nodes'].append({
                    'id': child_node.id,
                    'label': child_node.name,
                    'type': child_node.node_type.name,
                    'level': resourceLevel,
                    'sectorLevel': sectorLevel,
                    'relatedTagLevel': related_tag_level,
                    'num_related_tags': num_related_tags,
                    
                    #'num_sectors1': child_node.num_sectors1,
                })
                
        elif child_node.node_type.name == NodeType.TAG_CLUSTER:
            
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
                    data['child_nodes'].append({
                        'id': child_node.id,
                        'label': child_node.name,
                        'type': child_node.node_type.name,
                        'num_child_tags': num_child_tags,
                        
                        #'num_related_tags': num_related_tags,
                        #'num_sectors1': child_node.num_sectors1,
                    })
        
        else:
            raise Exception('Unknown child node type "%s" for node "%s"' % (child_node.node_type.name, child_node.name))
            
    json = simplejson.dumps(data, sort_keys=True, indent=4)
    
    #log('~ajax_nodes_json()')
    
    return HttpResponse(json, mimetype='text/plain')

@login_required
def ajax_nodes_xml(request):
    "Creates an XML list of nodes & connections for Asterisq Constellation Roamer"
    
    log('ajax_nodes_xml()')
    
    nodeId = request.GET['nodeId']
    log('  url: ' + request.get_full_path())
    
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
            if child_node.node_type.name == NodeType.TAG_CLUSTER or (child_node.num_societies1 > 0 and child_node.num_resources1 > 0):
                childNodes1.append(child_node)
        child_nodes = childNodes1
    
    # The main node
    nodes = [node]
    
    # Add the node's children
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
            if related_tag.societies.count() > 0 and related_tag.resources.count() > 0:
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
    
    doc = minidom.Document()
    
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
    
    for node1 in nodes:
        nodeElem = doc.createElement('node')
        nodeElem.setAttribute('id', str(node1.id))
        
        if node1.node_type.name == NodeType.TAG_CLUSTER:
            # For a cluster, show the short name "Cluster" if we're viewing the cluster or its parent.  Otherwise, show the full name "Cluster (Sector)".
            if node.id != node1.id and node.id != node1.get_sector().id:
                nodeElem.setAttribute('label', node1.get_full_cluster_name())
            else:
                nodeElem.setAttribute('label', node1.name)
        else:
            # None-cluster
            nodeElem.setAttribute('label', node1.name)
        nodeElem.setAttribute('depth_loaded', str(2))
        
        nodeElem.setAttribute('graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
        nodeElem.setAttribute('selected_graphic_fill_color', ROAMER_NODE_COLORS[node1.node_type.name] )
        nodeElem.setAttribute('graphic_border_color', GRAPHIC_BORDER_COLOR)
        nodeElem.setAttribute('graphic_type', 'shape')
        
        
        if node1.node_type.name == NodeType.ROOT:
            nodeElem.setAttribute('graphic_shape', 'circle')
        elif node1.node_type.name == NodeType.SECTOR:
            nodeElem.setAttribute('graphic_shape', 'circle')
        elif node1.node_type.name == NodeType.TAG_CLUSTER:
            nodeElem.setAttribute('graphic_shape', 'pentagon')
        elif node1.node_type.name == NodeType.TAG:
            nodeElem.setAttribute('graphic_shape', 'square')
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
    #    log('XML: ----------')
    #    log(doc.toprettyxml())
    #    log('---------------')
    
    #return HttpResponse(doc.toprettyxml(), 'text/plain')
    return HttpResponse(doc.toprettyxml(), 'text/xml')

@login_required
def tooltip(request, tag_id, parent_id):
    
    log('tooltip()')
    
    #sector_id = request.GET['sector_id']
    
    #tag = Node.objects.get(id=tag_id)
    tag = Node.objects.filter(id=tag_id)
    tag = Node.objects.get_extra_info(tag)
    tag = single_row(tag)
    
    log('  tag.parents.all(): %s' % tag.parents.all())
    log('  tag.num_parents1: %s' % tag.num_parents1)

    log('  tag.get_sectors(): %s' % tag.get_sectors())
    log('  tag.num_sectors1: %s' % tag.num_sectors1)
    
    #log('  tag.get_clusters(): %s' % tag.get_parent_clusters())
    #log('  tag.num_clusters1: %s' % tag.num_clusters1)
    
    #sector = single_row(tag.parents.filter(id=sector_id))
    parent = Node.objects.get(id=parent_id)
    
    log('  parent: %s' % parent)
    log('  parent.node_type.name: %s' % parent.node_type.name)
    
    (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags) = Node.objects.get_sector_ranges(parent)
    
    num_related_tags = tag.get_filtered_related_tag_count()
    
    resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources1)
    sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.num_sectors1)
    related_tag_level = _get_popularity_level(min_related_tags, max_related_tags, num_related_tags)

    log('  sectorLevel: %s' % sectorLevel)
    
    # Filter out related tags without filters (to match roamer)
    related_tags = []
    for related_tag in tag.related_tags.all():
        if related_tag.filters.count() > 0 and related_tag.resources.count() > 0:
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
    log('debug_send_email()')
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