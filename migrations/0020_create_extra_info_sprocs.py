# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        db.execute("""
CREATE FUNCTION child_societies_sum_or_avg (nodeId INT)
RETURNS INT
READS SQL DATA
BEGIN
SET @ret := 0; 
SET @node_type_id := 0;
SELECT node_type_id INTO @node_type_id FROM ieeetags_node WHERE id = nodeId;

IF @node_type_id = 3 THEN
            SELECT COUNT(id) INTO @ret
            FROM ieeetags_node_societies
            WHERE ieeetags_node_societies.node_id = nodeId;
ELSE
            SELECT AVG(child_societies.num_count) INTO @ret FROM (
                SELECT COUNT(*) as num_count, ieeetags_node_societies.node_id as nodeId2
                FROM ieeetags_node_societies
                GROUP BY ieeetags_node_societies.node_id
            ) AS child_societies WHERE nodeId2 = nodeId;
END IF;
RETURN(@ret);
END
""")

        db.execute("""
CREATE FUNCTION child_resources_sum_or_avg (nodeId INT)RETURNS INT
READS SQL DATA
BEGIN
SET @ret := 0; 
SET @node_type_id := 0;
SELECT node_type_id INTO @node_type_id FROM ieeetags_node WHERE id = nodeId;

IF @node_type_id = 3 THEN
            SELECT COUNT(id) INTO @ret
            FROM ieeetags_resource_nodes
            WHERE ieeetags_resource_nodes.node_id = nodeId;
ELSE
            SELECT AVG(IFNULL(child_resources.num_count, 0)) INTO @ret FROM (
                SELECT COUNT(*) as num_count, ieeetags_resource_nodes.node_id as nodeId2
                FROM ieeetags_resource_nodes
                GROUP BY ieeetags_resource_nodes.node_id
            ) AS child_resources WHERE nodeId2 = nodeId;
END IF;
RETURN(IFNULL(@ret, 0));
END
""")

        db.execute("""
CREATE FUNCTION related_tags_sum_or_avg (nodeId INT)RETURNS INT
READS SQL DATA
BEGIN
SET @ret := 0; 
SET @node_type_id := 0;
SELECT node_type_id INTO @node_type_id FROM ieeetags_node WHERE id = nodeId;

if @node_type_id = 3 THEN
            SELECT COUNT(id) INTO @ret
            FROM ieeetags_node_related_tags
            WHERE ieeetags_node_related_tags.from_node_id = nodeId;
ELSE
            SELECT AVG(IFNULL(child_related_tags.num_count,0)) INTO @ret FROM (
                SELECT COUNT(*) as num_count, ieeetags_node_related_tags.from_node_id AS nodeId2
                FROM ieeetags_node_related_tags
                GROUP BY ieeetags_node_related_tags.from_node_id
            ) AS child_related_tags WHERE nodeId2 = nodeId;
END IF;
RETURN(IFNULL(@ret, 0));
END
""")



        db.execute("""
CREATE FUNCTION sectors_sum_or_avg (nodeId INT)
RETURNS INT
READS SQL DATA
BEGIN
SET @ret := 0; 
SET @node_type_id := 0;
SELECT node_type_id INTO @node_type_id FROM ieeetags_node WHERE id = nodeId;
if @node_type_id = 3 THEN
            SELECT COUNT(*) INTO @ret
            FROM ieeetags_node_parents
            INNER JOIN ieeetags_node as parent
            ON ieeetags_node_parents.to_node_id = parent.id
            WHERE ieeetags_node_parents.from_node_id = nodeId
            AND parent.node_type_id =  2;
ELSE
            SELECT AVG(IFNULL(child_sectors.num_count,0)) INTO @ret FROM (
                SELECT COUNT(*) as num_count, n.id as nodeId2
                FROM ieeetags_node n
                CROSS JOIN ieeetags_node_parents xp
                ON n.id = xp.from_node_id
                AND n.node_type_id = 2
                GROUP BY n.id
            ) AS child_sectors WHERE nodeId2 = nodeId;
END IF;
RETURN(IFNULL(@ret, 0));
END   
""")

#        db.execute("""
#CREATE PROCEDURE get_extra_info (nodeId INT)
#
#""")

    def backwards(self, orm):
        db.execute("DROP FUNCTION child_societies_sum_or_avg")
        db.execute("DROP FUNCTION child_resources_sum_or_avg")
        db.execute("DROP FUNCTION related_tags_sum_or_avg")
        db.execute("DROP FUNCTION sectors_sum_or_avg")                   
