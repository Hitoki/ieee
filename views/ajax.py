from decorators import optional_login_required as login_required
from django.views.decorators.csrf import csrf_exempt


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
    jobsCount = "0"

    if request.META['HTTP_REFERER'].endswith('/textui_new'):
        NEWUI = True
    else:
        NEWUI = False
    context['NEWUI'] = NEWUI

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

    #experts = Resource.objects.getForNode(tag, resourceType=ResourceType.EXPERT)
    #counts += experts.count()
    #context['experts'] = experts

    # Grab standards with is_machine_generated field.
    if tab == 'standard':
        standards_resource_nodes = tag.resource_nodes.filter(resource__resource_type__name=ResourceType.STANDARD)
        standards = []
        for standards_resource_node in standards_resource_nodes:
            standard = standards_resource_node.resource
            standard.is_machine_generated = standards_resource_node.is_machine_generated
            standards.append(standard)

        counts += len(standards)
        context['standards'] = standards
        tab_template = 'ajax_standard_tab.inc.html'
        context['loaded'] = True

    if tab == 'periodical':
        # Grab periodicals with is_machine_generated field.
        periodicals_resource_nodes = tag.resource_nodes.filter(resource__resource_type__name=ResourceType.PERIODICAL)
        periodicals = []
        for periodicals_resource_node in periodicals_resource_nodes:
            periodical = periodicals_resource_node.resource
            periodical.is_machine_generated = periodicals_resource_node.is_machine_generated
            periodicals.append(periodical)

        counts += len(periodicals)            
        context['periodicals'] = periodicals
        tab_template = 'ajax_periodical_tab.inc.html'
        context['loaded'] = True
        
    if tab == 'conference':    
        # Sort the conferences by year latest to earliest.
        conferences_resource_nodes = tag.resource_nodes.filter(resource__resource_type__name=ResourceType.CONFERENCE)
        conferences = []
        for conferences_resource_node in conferences_resource_nodes:
            conference = conferences_resource_node.resource
            conference.is_machine_generated = conferences_resource_node.is_machine_generated
            if not re.compile('^https?://').match(conference.url):
                conference.url = 'http://' + conference.url
            conferences.append(conference)
        
        conferences = list(sorted(conferences, key=lambda resource: resource.year, reverse=True))
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

    if tab == 'job':
        jobsUrl = "http://jobs.ieee.org/jobs/search/results?%s&rows=25&format=json" % urllib.urlencode({"kwsMustContain": tag.name})
        file1 = urllib2.urlopen(jobsUrl).read()
        jobsJson = json.loads(file1)
        jobsCount = jobsJson.get('Total')
        #jobs = jobsJson.get('Jobs')
        #jobsHtml = ""
        #for job in jobs:
        #    jobsHtml = jobsHtml + '<a href="%(Url)s" target="_blank" class="featured"><b>%(JobTitle)s</b></a> %(Company)s<br>\n' % job

        #if len(jobsHtml):
        #    jobsHtml = jobsHtml + '<a href="%s" target="_blank">More jobs</a>' % jobsUrl.replace('&format=json','')

        jobsUrl = jobsUrl.replace('&format=json','')
        tab_template = 'ajax_job_tab.inc.html'
        context['jobsCount'] = jobsCount
        context['jobsUrl'] = jobsUrl        
        context['loaded'] = True

    if tab == 'overview':        
        #try:
            #xplore_article = ajax_recent_xplore(tag.name)
            #xplore_article = _get_xplore_results(tag.name, show_all=False, offset=0, sort=XPLORE_SORT_PUBLICATION_YEAR, sort_desc=True, recent=True)[0][0]
        #except IndexError:
        #    xplore_article = None

        #context['xplore_article'] = xplore_article
        context['close_conference'] = tag._get_closest_conference()
        context['definition'] = tag._get_definition_link()
        tab_template = 'ajax_over_tab.inc.html'

    file1 = None
    # removied sectors from count
    num_related_items =  \
        counts \
        + clusters1.count() \
        + tag.related_tags.count() 

    #context['num_related_items'] = num_related_items

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
    
    #jobs_results, jobs_error, num_results = _get_xplore_results(name, show_all=show_all, offset=offset, sort=sort, sort_desc=sort_desc, ctype=ctype)
        
    jobsUrl = "http://jobs.ieee.org/jobs/search/results?%s&rows=25&page=%s&format=json" % (urllib.urlencode({"kwsMustContain": tag.name}), offset)
    file1 = urllib2.urlopen(jobsUrl).read()
    jobsJson = json.loads(file1)
    jobsCount = jobsJson.get('Total')
    jobs = jobsJson.get('Jobs')
    jobsHtml = ""
    for job in jobs:
        jobsHtml = jobsHtml + '<a href="%(Url)s" target="_blank" class="featured"><b>%(JobTitle)s</b></a> %(Company)s<br>\n' % job
    
    # DEBUG:
    #xplore_error = 'BAD ERROR.'

    data = {
        'num_results': jobsCount,
        'html': jobsHtml,
        'search_term': name,
        'token': token,
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
    @param token: The unique token for this request, used in JS to ignore overlapping AJAX requests.
    @param sector_id: (Optional) The sector to filter results.
    @param society_id: (Optional) The society to filter results.
    @param cluster_id: (Optional) The cluster to filter results, used to filter "search_for" results.
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
    
    textui_flyovers_url = reverse('tooltip') + '/tagid?' + urllib.urlencode(params)
    # The tooltip url needs to know if 'all' societies or sectors is chosen.
    # Otherwise the color blocks in the tooltip will all be red.
    if request.GET.get('society_id', None) == "all":
        textui_flyovers_url = textui_flyovers_url.replace('society_id=null', 'society_id=all')
    if request.GET.get('sector_id', None) == "all":
        textui_flyovers_url = textui_flyovers_url.replace('parent_id=null', 'parent_id=all')
    
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
            non_matches = soup.findAll('a', text=lambda text: search_for not in text)
            for nm in non_matches:
                if nm.findParent('div'):
                    nm.findParent('div').extract()
            cache = nm.join('')
        cache_params["search_for"] = search_for
            
    # Still no Cache so let's go to the DB.
    if not cache:
        # Create the cache if it doesn't already exist.
        print 'CACHE MISS: Creating new cache page.'
        content, node_count_content = _render_textui_nodes(request, sort, search_for, sector_id, sector, society_id, society, cluster_id, cluster, show_clusters, show_terms, request.user.is_staff, page)
        cache_content = json.dumps({
            'content': content,
            'node_count_content': node_count_content,
        })
        cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)
    else:
        #print 'CACHE HIT.'
        cache_content = json.loads(cache.content)
        content, node_count_content = cache_content['content'], cache_content['node_count_content']
    
    return HttpResponse(json.dumps({
        'token': token,
        'search_for': search_for,
        'content': content,
        'node_count_content': node_count_content,
        'textui_flyovers_url': textui_flyovers_url,
    }), 'text/plain')


def ajax_nodes_json(request):
    "Create a JSON collection for API"
    if not 's' in request.GET or not len(request.GET['s'].strip()):
        return HttpResponse("{'error': 'no search term provided'}", content_type='application/javascript; charset=utf8')

    search_words = re.split(r'\s', request.GET['s'])
    from django.db.models import Q
    queries = None
    for word in search_words:
        if queries is None:
            queries = Q(name__icontains=word)
        else:
            queries &= Q(name__icontains=word)
    
    nodes = Node.objects.filter(queries)
    from django.core import serializers
    json = serializers.serialize("json", nodes, ensure_ascii=False, fields=('id', 'name'))
    json = json.replace(', "model": "ieeetags.node"', '')
    return HttpResponse(json, content_type='application/javascript; charset=utf8')


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

@csrf_exempt
def ajax_notification_request(request):
    rnnr = ResourceAdditionNotificationRequest()
    rnnr.email = request.POST['email']
    rnnr.date_created = datetime.datetime.now()
    rnnr.node = Node.objects.get(id=request.POST['nodeid'])
    rnnr.save()

    return HttpResponse('success')

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
        node = Node.objects.get_extra_info(node)
        node = single_row(node)
        
        #print '  node.node_type.name: %r' % node.node_type.name
        
        if node.node_type.name == NodeType.TAG:
            
            tag = node
            
            # Normal Tag
            
            if parent_id is not None:
                if parent_id == "all":
                    if not settings.DEBUG:
                        # Temporary fix for production since tooltip queries for 'all' are too slow
                        parent = Node.objects.filter(node_type__name=NodeType.SECTOR)[0]
                        tags = parent.child_nodes
                    else:     
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
                    # Temporary fix for production since tooltip queries for 'all' are too slow
                    if not settings.DEBUG:
                        fake_society= Society.objects.all()[0]
                        (min_resources, max_resources, min_sectors, max_sectors, min_related_tags, max_related_tags, min_societies, max_societies) = fake_society.get_tag_ranges()
                        (min_score, max_score) = fake_society.get_combined_ranges()

                    else:
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
                            if max_resources is None or tag1['num_resources1'] > max_resources:
                                max_resources = tag1['num_resources1']
                            if min_sectors is None or tag1['num_sectors1'] < min_sectors:
                                print "new min"
                                min_sectors = tag1['num_sectors1']
                            if max_sectors is None or tag1['num_sectors1'] > max_sectors:
                                print "new max"
                                max_sectors = tag1['num_sectors1']
                            if min_related_tags is None or tag1['num_related_tags1'] > min_related_tags:
                                min_related_tags = tag1['num_related_tags1']
                            if max_related_tags is None or tag1['num_related_tags1'] < max_related_tags:
                                max_related_tags = tag1['num_related_tags1']
                            if min_societies is None or tag1['num_societies1'] > min_societies:
                                min_societies = tag1['num_societies1']
                            if max_societies is None or tag1['num_societies1'] < max_societies:
                                max_societies = tag1['num_societies1']
                            if min_score is None or tag1['score1'] > min_score:
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
            
            tagLevel = _get_popularity_level(min_score, max_score, node.score1)
            
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

