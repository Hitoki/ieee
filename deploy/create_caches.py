from ieeetags.models import Cache, Society
from ieeetags.views.ajax import _render_textui_nodes
import simplejson as json
from new_models.node import Node
from new_models.types import NodeType
from noomake import *

def main():
    print 'Starting to create caches...'


    insert_cache(None, None, 'sector')
    insert_cache(None, None, 'society')

    sectors = Node.objects.filter(node_type__name=NodeType.SECTOR)
    for sector in sectors:
        print 'Creating cache for Sector %s sorted by %s' % (sector.name, 'sort')
        insert_cache(sector, None, 'sector')

    societies = Society.objects.all()
    for society in societies:
        print 'Creating cache for Organization/Society %s sorted by %s' % (society.name, 'sort')
        insert_cache(None, society, 'society')

def insert_cache(sector, society, page):

    cache_params = {
        'sector_id': sector and sector.id or None,
        'society_id': society and society.id or None,
        'cluster_id': None,
        'search_for': None,
        'sort': 'connectedness',
        'page': page,
        'show_clusters': True,
        'show_terms': True,
    }

    sorts = ('connectedness', 'alphabetical', 'frequency', 'num_sectors', 'num_related_tags', 'num_societies')
    for sort in sorts:
        cache_params['sort'] = sort
        content, node_count_content = _render_textui_nodes(sort, None, sector and sector.id or None, sector, society and society.id or None, society, None, None, True, True, False, page)
        cache_content = json.dumps({
                'content': content,
                'node_count_content': node_count_content,
                })
        cache = Cache.objects.set('ajax_textui_nodes', cache_params, cache_content)
        
if __name__ == '__main__':
    main()
