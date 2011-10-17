import sys, os
from datetime import datetime
from urllib import quote
from SPARQLWrapper import SPARQLWrapper, JSON
from ieeetags.models import *
from django.db.models import Q


def main(*args):
    sparql_pat = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    SELECT ?comment
    WHERE { <http://dbpedia.org/resource/%s> rdfs:comment ?comment 
    FILTER langMatches( lang(?comment), "EN" )
    }
    """

    tags = Node.objects.filter(node_type__name=NodeType.TAG).filter(
        Q(name__gte="Magnetic_semiconductors")
        &
        (
            Q(definition__isnull=True)
            | (
                Q(definition__icontains='wikipedia')
                | Q(definition_updated_when__isnull=True)
                )
            )
        ).order_by('name')


    
    print "Processing %d tags." % tags.count()

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    for tag in tags[10:]:
        print tag.name
        query = sparql_pat  % quote(tag.name.replace(' ', '_'))
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        results = sparql.query().convert()
        #import ipdb; ipdb.set_trace()
        try:
            tag.definition = results['results']['bindings'][0]['comment']['value']
            tag.definition_source = 'dbpedia.org'
            tag.definition_updated_when = datetime.now()
            tag.save()
        except IndexError:
            continue
        except:
            print sys.exec_info()[:2]
            continue


if __name__ == "__main__":
    sys.exit(main(*sys.argv))
