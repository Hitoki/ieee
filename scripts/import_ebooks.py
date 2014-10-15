from sys import argv
import csv

from django.db.utils import IntegrityError

from dateutil import parser
from webapp.models.node import Node
from webapp.models.resource import Resource, ResourceNodes
from webapp.models.society import Society
from webapp.models.types import NodeType, ResourceType


script, filepath = argv

reader = csv.reader(open(filepath, "rb"))

for row in reader:
    if reader.line_num <= 1:
        continue
    rrr = Resource()
    rrr.resource_type = ResourceType.objects.get(name="ebook")
    rrr.ieee_id = row[1]
    rrr.name = row[2]
    rrr.description = row[3]
    rrr.url = row[4]
    rrr.keywords = row[10]
    rrr.priority_to_tag = (row[11].lower() == 'yes')
    rrr.completed = (row[12].lower() == 'yes')
    rrr.date = parser.parse(row[15])
    rrr.save()

    tag_names = row[5].replace('"', '').split('|')
    for tag_name in tag_names:
        tag_name = tag_name.strip()
        print tag_name
        try:
            tag = Node.objects.get(node_type=NodeType.objects.getFromName(NodeType.TAG),name=tag_name)
            rn = ResourceNodes(resource=rrr, node=tag)
            rn.save()
        except Node.DoesNotExist:
            pass
        except IntegrityError:
            pass

    soc_names = row[6].replace('"', '').split('|')
    for soc_name in soc_names:
        soc_name = soc_name.strip()
        print soc_name
        try:
            soc = Society.objects.get(abbreviation=soc_name)
            rrr.societies.add(soc)
        except Node.DoesNotExist:
            pass


    rrr.save()


