from sys import argv
import csv
import MySQLdb
from new_models.node import Node
from new_models.types import NodeType


script, filepath = argv

host = 'localhost'
user = 'root'
pw = 'root'
db = 'ieeetagsnewdev'

mydb = MySQLdb.connect (host = host,
                 user = user,
                 passwd = pw,
                 db = db)

cursor = mydb.cursor()
fp = open(filepath, "rb")
reader = csv.reader(fp)

added_clusters = []
# for row in reader:
#     if reader.line_num == 1:
#         continue

#     new_cluster = row[6] == "1"
#     if new_cluster and not new_cluster in added_clusters:
#         new_cluster_name = row[4]
#         cursor.execute('INSERT into ieeetags_node (name, node_type_id, is_taxonomy_term) values ("%s", 4, 0);', (new_cluster_name, ))
#         added_clusters.append(new_cluster_name)

# fp.close()
# fp = open(filepath, "rb")
# reader = csv.reader(fp)
for row in reader:
    if reader.line_num == 1:
        continue

    id = int(row[0])
    old_name = row[1].replace("'", "").strip()
    action = row[2]
    new_name = row[3]
    try:
        cluster_id = int(row[5])
    except ValueError:
        cluster_id = None
    cluster_name = row[4]
    new_cluster = row[6] == "1"

    if action == 'D':
        Node.objects.get(id=id, name=old_name).delete()
        #cursor.execute('DELETE from ieeetags_node where id = %s and name = "%s"; ', (id, old_name, ))
        continue
    if 'R' in action:
        nnn = Node.objects.get(id=id, name=old_name)
        nnn.name = new_name
        nnn.save()
        #cursor.execute('UPDATE ieeetags_node set name = "%s" where id = %s and name = "%s"; ', (new_name, id, old_name))
        #mydb.commit()
    if 'C' in action:
        print "old name: %s" % old_name
        nnn = Node.objects.get(id=id, name=old_name)
        nnn.parents.delete()
        #rc_sql = 'DELETE from ieeetags_node_parents where from_node_id = %s; ';
        #cursor.execute(rc_sql);
        #mydb.commit()
        if new_cluster and not new_cluster in added_clusters:
            nc = Node()
            nc.name = cluster_name
            nc.node_type = NodeType.getFromName(NodeType.TAG_CLUSTER)
            nc.is_taxonomy_term = False
            nc.save()
            added_clusters.append(cluster_name)
        else:
            nc = Node.objects.get(id=cluster_id, node_type=NodeType.getFromName(NodeType.TAG_CLUSTER))

        nnn.parents.add(nc)
        nnn.save()
            #rc_sql = rc_'INSERT INTO ieeetags_node_parents (from_node_id, to_node_id) values (%s, (select id from ieeetags_node where name="%s" and node_type_id = 4));'
            #cursor.execute(rc_sql, (id, id, cluster_name))
        #else:
            #rc_sql = rc_sql + 'INSERT INTO ieeetags_node_parents (from_node_id, to_node_id) values (%s, %s);'
            #cursor.execute(rc_sql, (id, id, cluster_id))
        #mydb.commit()



#mydb.rollback()
#mydb.commit()

#cursor.close()    
