from ieeetags.models import Cache, Node, NodeType, Society
from ieeetags.views import _render_textui_nodes
import simplejson as json

def main():
    print 'Starting to create caches...'

    sorts = ('connectedness', 'alphabetical', 'frequency', 'num_sectors', 'num_related_tags', 'num_societies')

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
        for sort in sorts:
            print 'Creating cache for Sector %s sorted by %s' % sector.name, sort
            cache_params['sector_id'] = sector.id
            cache_params['page'] = 'sector'
            cache_params['sort'] = sort
            content, node_count_content = _render_textui_nodes(sort, None, sector.id, sector, None, None, None, None, True, True, False, 'sector')
            cache_content = json.dumps({
                    'content': content,
                    'node_count_content': node_count_content,
                    })
            cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)

    orgs = Society.objects.all()
    for org in orgs:
        for sort in sorts:
            print 'Creating cache for Organization/Society: %s' % org.name
            cache_params['sector_id'] = None
            cache_params['society_id'] = org.id
            cache_params['page'] = 'society'
            cache_params['sort'] = sort
            content, node_count_content = _render_textui_nodes(sort, None, None, None, org.id, org, None, None, True, True, False, 'society')
            cache_content = json.dumps({
                    'content': content,
                    'node_count_content': node_count_content,
                    })
            cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)


    #societies = Society.objects.all()
    #for society in societies:
        
if __name__ == '__main__':
    main()
