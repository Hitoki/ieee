from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from xml.dom import minidom
import logging
import os.path
import string
from urllib import quote

from ieeetags.models import single_row, Filter, Node, NodeType, Resource, ResourceType, Society
from ieeetags.forms import *
import settings
import util

# Using this instead of 'render_to_response' adds our context processors, which add things like MEDIA_URL to the page automatically.
def render(request, template, dictionary=None):
    return render_to_response(template, dictionary=dictionary, context_instance=RequestContext(request))

# ------------------------------------------------------------------------------

def index(request):
    return render(request, 'index.html')

def roamer(request):
    nodeId = request.GET.get('nodeId', Node.objects.getRoot().id)
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    return render(request, 'roamer.html', {
        'nodeId':nodeId,
        'sectors':sectors,
        'filters':filters,
    })

def textui(request):
    sectorId = request.GET.get('nodeId', Node.objects.getFirstSector().id)
    node = Node.objects.get(id=sectorId)
    
    # Double check to make sure we didn't get a root or tag node
    if node.node_type.name == 'root':
        sectorId = Node.objects.getFirstSector().id
    elif node.node_type.name == 'tag':
        sectorId = node.parent.id
    
    sectors = Node.objects.getSectors()
    filters = Filter.objects.all()
    
    return render(request, 'textui.html', {
        'sectorId':sectorId,
        'sectors':sectors,
        'filters':filters,
    })

def feedback(request):
    if request.method == 'GET':
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
            send_from = 'admin@demo.systemicist.com'
            send_to = [
                'jamesyoneda@thoughtcap.com',
                'atear@aptuscollaborative.com',
                'jacktemplin@noospheremedia.com',
            ]
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
        
    conferences = Resource.objects.getForNode(tag, resourceType=ResourceType.CONFERENCE)
    experts = Resource.objects.getForNode(tag, resourceType=ResourceType.EXPERT)
    periodicals = Resource.objects.getForNode(tag, resourceType=ResourceType.PERIODICAL)
    standards = Resource.objects.getForNode(tag, resourceType=ResourceType.STANDARD)
    
    return render(request, 'content.html', {
        'tag':tag,
        'iconSocieties': iconSocieties,
        'noIconSocieties': noIconSocieties,
        'conferences': conferences,
        'experts': experts,
        'periodicals': periodicals,
        'standards': standards,
    })

def ajax_node(request):
    nodeId = request.GET['nodeId']
    node = Node.objects.get(id=nodeId)
    if node.parent is None:
        parentName = None
    else:
        parentName = node.parent.name
    
    data = {
        'id': node.id,
        'name': node.name,
        'type': node.node_type.name,
    }
    
    if node.parent is not None:
        data['parent'] = {
            'id': node.parent.id,
            'name': node.parent.name,
        }
    
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

def ajax_nodes_json(request):
    sectorId = request.GET['sectorId']
    sort = request.GET.get('sort')
    filterValues = request.GET.get('filterValues')
    
    #print 'filterValues:', filterValues
    
    if sort is None or sort == 'alphabetical':
        orderBy = 'name'
    elif sort == 'frequency':
        orderBy = 'num_resources'
    #elif sort == 'num_sectors':
    #    orderBy = 'parents'
    else:
        raise Exception('Unrecognized sort "%s"' % sort)
    
    filterIds = []
    if filterValues != '':
        for filterValue in filterValues.split(','):
            #print 'filterValue:', filterValue
            #filterIds.append(Filter.objects.getFromValue(filterValue))
            filterIds.append(Filter.objects.getFromValue(filterValue).id)
    
    #print 'filterIds:', filterIds
    
    # Build node list
    sector = Node.objects.get(id=sectorId)
    tags = sector.child_nodes.order_by(orderBy)
    #tags = Node.objects.filter(parent=sector).order_by(orderBy)
    
    (minResources, maxResources) = Node.objects.get_resource_range(sector)
    (min_sectors, max_sectors) = Node.objects.get_sector_range(sector)
    
    # JSON Output
    data = []
    for tag in tags:
        #print 'tag.name:', tag.name
        resourceLevel = _get_popularity_level(minResources, maxResources, tag.num_resources)
        sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.parents.count())
        
        # TODO:
        relatedTagLevel = 'level1'
        
        if len(tag.filters.filter(id__in=filterIds)):
            data.append({
                'id': tag.id,
                'label': tag.name,
                'type': tag.node_type.name,
                'level': resourceLevel,
                'sectorLevel': sectorLevel,
                'relatedTagLevel': relatedTagLevel,
            })
            
    json = simplejson.dumps(data, sort_keys=True, indent=4)
    return HttpResponse(json, mimetype='text/plain')

def ajax_nodes_xml(request):
    #print 'ajax_nodes_xml()'
    
    nodeId = request.GET['nodeId']
    #print '  nodeId: ' + nodeId
    
    # TODO: the depth param is ignored, doesn't seem to affect anything now
    
    # Build node list
    node = Node.objects.get(id=nodeId)
    childNodes = Node.objects.getChildNodes(node)
    
    nodes = [node]
    nodes.extend(childNodes)
    if node.parent is not None:
        nodes.append(node.parent)
    
    #print '  node:', node
    #print '  len(childNodes):', len(childNodes)
    #print '  len(nodes):', len(nodes)
    
    
    edges = []
    for childNode in childNodes:
        edges.append((node.id, childNode.id))
    if node.parent is not None:
        edges.append((node.parent.id, node.id))
        
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

def tooltip(request):
    tag_id = request.GET['tag_id']
    sector_id = request.GET['sector_id']
    
    tag = Node.objects.get(id=tag_id)
    sector = single_row(tag.parents.filter(id=sector_id))

    (min_resources, max_resources) = Node.objects.get_resource_range(sector)
    (min_sectors, max_sectors) = Node.objects.get_sector_range(sector)
    
    resourceLevel = _get_popularity_level(min_resources, max_resources, tag.num_resources)
    sectorLevel = _get_popularity_level(min_sectors, max_sectors, tag.parents.count())
    # TODO:
    #relatedTags = ['test', 'test']
    relatedTagLevel = 'level1'
    
    return render(request, 'tooltip.html', {
        'tag': tag,
        'tagLevel': resourceLevel,
        'sectorLevel': sectorLevel,
        #'limits': limits,
        #'relatedTags': relatedTags,
        'relatedTagLevel': relatedTagLevel,
    })

def ajax_search_tags(request):
    #MAX_RESULTS = 50
    
    search_for = request.GET['search_for']
    #tags = Node.objects.searchTagsByNameSubstring(search_for)[:MAX_RESULTS+1]
    tags = Node.objects.searchTagsByNameSubstring(search_for)
    
    #if len(tags) > MAX_RESULTS:
    #    tags = tags[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if tags:
        for tag in tags:
            data['options'].append({
                'name': tag.name,
                'name_link': reverse('admin_edit_tag', args=[tag.id]) + '?return_url=%s' % quote('/admin/?hash=' + quote('#tab-tags-tab')),
                'value': tag.id,
                'tag_name': tag.name,
                'sector_names': tag.parent_names(),
                'num_societies': len(tag.societies.all()),
                'num_related_tags': len(tag.related_tags.all()),
                'num_filters': len(tag.filters.all()),
                'num_resources': len(tag.resources.all()),
            })
    
    return HttpResponse(simplejson.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")

def ajax_search_resources(request):
    #MAX_RESULTS = 50
    
    search_for = request.GET['search_for']
    #resources = Resource.objects.searchByNameSubstring(search_for)[:MAX_RESULTS+1]
    resources = Resource.objects.searchByNameSubstring(search_for)
    
    #if len(resources) > MAX_RESULTS:
    #    resources = resources[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if resources:
        for resource in resources:
            data['options'].append({
                'name': resource.name,
                'value': resource.id,
            })
    
    return HttpResponse(simplejson.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")

def ajax_search_societies(request):
    #MAX_RESULTS = 50
    
    search_for = request.GET['search_for']
    #societies = Society.objects.searchByNameSubstring(search_for)[:MAX_RESULTS+1]
    societies = Society.objects.searchByNameSubstring(search_for)
    
    #if len(societies) > MAX_RESULTS:
    #    societies = societies[:MAX_RESULTS]
    #    more_results = True
    #else:
    more_results = False
    
    data = {
        'search_for': search_for,
        'more_results': more_results,
        'options': [],
    }
    if societies:
        for society in societies:
            data['options'].append({
                'name': society.name,
                'value': society.id,
            })
    
    return HttpResponse(simplejson.dumps(data, sort_keys=True, indent=4), mimetype="text/plain")
    
def ajax_update_society(request):
    action = request.POST.get('action')
    society_id = request.POST.get('society_id')
    tag_id = request.POST.get('tag_id')
    
    if action == 'add_tag':
        society = Society.objects.get(id=society_id)
        tag = Node.objects.get(id=tag_id)
        society.tags.add(tag)
        return HttpResponse('success')
    
    elif action == 'remove_tag':
        society = Society.objects.get(id=society_id)
        tag = Node.objects.get(id=tag_id)
        society.tags.remove(tag)
        return HttpResponse('success')
    
    else:
        raise Exception('Unknown action "%s"' % action)
