from ieeetags.models import Cache, Node, NodeType, Society
from ieeetags.views import _render_textui_nodes
import simplejson as json

def main():
    print 'Starting to create caches...'
    cache_params = {
        'sector_id': None,
        'society_id': None,
        'cluster_id': None,
        'search_for': None,
        'sort': 'connectedness',
        'page': '',
        'show_clusters': True,
        'show_terms': True,
    }

    sectors = Node.objects.filter(node_type__name=NodeType.SECTOR)
    for sector in sectors:
        print 'Creating cache for Sector: %s' % sector.name
        cache_params['sector_id'] = sector.id
        cache_params['page'] = 'sector'
        content, node_count_content = _render_textui_nodes('connectedness', None, sector.id, sector, None, None, None, None, True, True, False, 'sector')
        cache_content = json.dumps({
            'content': content,
            'node_count_content': node_count_content,
            })
        cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)

    orgs = Society.objects.all()
    for org in orgs:
        print 'Creating cache for Organization/Society: %s' % org.name
        cache_params['sector_id'] = None
        cache_params['society_id'] = org.id
        cache_params['page'] = 'society'
        content, node_count_content = _render_textui_nodes('connectedness', None, None, None, org.id, org, None, None, True, True, False, 'society')
        cache_content = json.dumps({
            'content': content,
            'node_count_content': node_count_content,
            })
        cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)


    #societies = Society.objects.all()
    #for society in societies:
        
if __name__ == '__main__':
    main()
