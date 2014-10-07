from webapp.models.types import NodeType


def get_node_extra_info(queryset, order_by=None, selected_filter_ids=None):
    """
    Returns the queryset with extra columns:
        num_resources1
        num_societies1
        num_filters1
        num_selected_filters1
        num_sectors1
        num_related_tags1
        num_parents1
        score1
    """
    tag_node_type_id = NodeType.objects.getFromName(NodeType.TAG).id
    sector_node_type_id = NodeType.objects.getFromName(NodeType.SECTOR).id
    cluster_node_type_id = NodeType.objects.getFromName(NodeType.TAG_CLUSTER).id

    if selected_filter_ids is not None:
        selected_filter_ids = [str(id) for id in selected_filter_ids]
        num_selected_filters1_sql = """
            SELECT Count(*)
            FROM ieeetags_node_filters
            WHERE ieeetags_node_filters.node_id = ieeetags_node.id
            AND ieeetags_node_filters.filter_id in (%s)
        """ % ','.join(selected_filter_ids)
    else:
        num_selected_filters1_sql = 'SELECT NULL'

    num_resources_sql = """
        -- Count of this tag's resources.
        IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
            (SELECT COUNT(*)
            FROM ieeetags_resource_nodes
            WHERE ieeetags_resource_nodes.node_id = ieeetags_node.id)
        ,
            (SELECT AVG(child_resources.num_count) FROM (
                SELECT COUNT(*) as num_count, ieeetags_resource_nodes.node_id as nodeId
                FROM ieeetags_resource_nodes
                GROUP BY ieeetags_resource_nodes.node_id
            ) AS child_resources WHERE nodeId = ieeetags_node.id )
        ),0)
    """ % {'tag_node_type_id': tag_node_type_id}

    num_societies_sql = """
        -- Count of this tag's societies
        IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
            (SELECT COUNT(*)
            FROM ieeetags_node_societies
            WHERE ieeetags_node_societies.node_id = ieeetags_node.id)
        ,
            (SELECT AVG(child_societies.num_count) FROM (
                SELECT COUNT(*) as num_count, ieeetags_node_societies.node_id as nodeId
                FROM ieeetags_node_societies
                GROUP BY ieeetags_node_societies.node_id
            ) AS child_societies WHERE nodeId = ieeetags_node.id)
        ),0)
    """ %{'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}

    num_filters_sql = 'SELECT COUNT(*) FROM ieeetags_node_filters WHERE ieeetags_node_filters.node_id = ieeetags_node.id'

    num_sectors_sql = """
        -- This tag's sectors.
        IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
            (SELECT COUNT(*)
            FROM ieeetags_node_parents
            INNER JOIN ieeetags_node as parent
            ON ieeetags_node_parents.to_node_id = parent.id
            WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id
            AND parent.node_type_id = %(sector_node_type_id)s)
        ,
            (SELECT AVG(child_sectors.num_count) FROM (
                SELECT COUNT(*) as num_count, n.id as nodeId
                FROM ieeetags_node n
                CROSS JOIN ieeetags_node_parents xp
                ON n.id = xp.from_node_id
                AND n.node_type_id = %(sector_node_type_id)s
                GROUP BY n.id
            ) AS child_sectors WHERE nodeId = ieeetags_node.id)
        ),0)
    """ % {'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}

    num_related_tags_sql = """
        -- Count of this tag's related tags
        IFNULL(IF(ieeetags_node.node_type_id = %(tag_node_type_id)s,
            (SELECT COUNT(*)
            FROM ieeetags_node_related_tags
            WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id)
        ,
           -- AVG of cluster's tags related tag count.
            (SELECT AVG(child_related_tags.num_count) FROM (
                SELECT COUNT(*) as num_count, ieeetags_node_related_tags.from_node_id AS nodeId
                FROM ieeetags_node_related_tags
                GROUP BY ieeetags_node_related_tags.from_node_id
            ) AS child_related_tags WHERE nodeId = ieeetags_node.id)
        ),0)
    """ % {'tag_node_type_id': tag_node_type_id, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id}

    return queryset.extra(
        select={
            'num_resources1': num_resources_sql,
            'num_societies1': num_societies_sql,
            'num_filters1': num_filters_sql,
            'num_selected_filters1': num_selected_filters1_sql,
            'num_sectors1': num_sectors_sql,
            #'num_clusters1': 'SELECT COUNT(*) FROM ieeetags_node_parents INNER JOIN ieeetags_node as parent on ieeetags_node_parents.to_node_id = parent.id WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id AND parent.node_type_id = %s' % (cluster_node_type_id),
            # TODO: Some of the related tags will be hidden (no resources, no filters, etc), so this count is off
            'num_related_tags1': num_related_tags_sql,
            'num_parents1': 'SELECT COUNT(*) FROM ieeetags_node_parents WHERE ieeetags_node_parents.from_node_id = ieeetags_node.id',
            'score1': """
                %(num_resources_sql)s
                +
                %(num_sectors_sql)s
                +
                %(num_related_tags_sql)s
                +
                %(num_societies_sql)s
                """ % {'num_resources_sql': num_resources_sql, 'num_societies_sql': num_societies_sql, 'num_sectors_sql': num_sectors_sql, 'num_related_tags_sql': num_related_tags_sql, 'cluster_node_type_id': cluster_node_type_id, 'sector_node_type_id': sector_node_type_id},
            #'filtered_num_related_tags1': """
            #    SELECT COUNT(ieeetags_node_related_tags.id) FROM ieeetags_node_related_tags WHERE ieeetags_node_related_tags.from_node_id = ieeetags_node.id
            #    """,
        },
        order_by=order_by,
    )
