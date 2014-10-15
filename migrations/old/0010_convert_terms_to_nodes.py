# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

#import util

class Migration(DataMigration):

    #@util.profiler
    def forwards(self, orm):
        'Converts all TaxonomyTerm objects into Node objects (ie. tags).'
        import time
        
        num_duplicates = 0
        num_converted = 0
        
        tag_type = orm.NodeType.objects.get(name='tag')
        cluster_type = orm.NodeType.objects.get(name='tag_cluster')
        
        tags = orm.Node.objects.filter(node_type=tag_type)
        num_tags = tags.count()
        tag_names = [tag.name for tag in tags]
        terms = orm.TaxonomyTerm.objects.all()
        num_terms = terms.count()
        
        num_valid_clusters = 0
        num_missing_clusters = 0
        
        start = time.time()
        last_update_time = start
        
        clusters = orm.Node.objects.filter(node_type=cluster_type)
        clusters2 = {}
        for cluster in clusters:
            clusters2[cluster.name] = cluster
        
        term_id_to_tag_list = {}
        
        for i, term in enumerate(terms):
            if term.name in tag_names:
                # Ignore duplicate.
                num_duplicates += 1
            else:
                tag = orm.Node()
                tag.name = term.name
                tag.node_type = tag_type
                tag.is_taxonomy_term = True
                tag.save()
                
                term_id_to_tag_list[term.id] = tag
                
                # NOTE: Delay assigning related_terms here, since we can do it faster afterward.
                #for term1 in term.related_terms.all():
                #    try:
                #        tag1 = orm.Node.objects.get(node_type=tag_type, name=term1.name)
                #        tag.related_tags.add(tag1)
                #    except orm.Node.DoesNotExist:
                #        # Ignore any missing terms, they'll be added later (since relationships are 2-way).
                #        pass
                
                for tag1 in term.related_nodes.all():
                    tag.related_tags.add(tag1)
                
                for taxonomy_cluster in term.taxonomy_clusters.all():
                    if taxonomy_cluster.name in clusters2:
                        cluster = clusters2[taxonomy_cluster.name]
                        tag.parents.add(cluster)
                        num_valid_clusters += 1
                    else:
                        # Ignore missing clusters for now.
                        num_missing_clusters += 1
                
                tag.save()
                
                # NODE FIELDS:
                #parents = models.ManyToManyField('self', symmetrical=False, related_name='child_nodes', null=True, blank=True)
                #societies = models.ManyToManyField('Society', related_name='tags', blank=True)
                #filters = models.ManyToManyField('Filter', related_name='nodes')
                #related_tags = models.ManyToManyField('self', null=True, blank=True)
                
                # TERM FIELDS:
                #related_nodes = models.ManyToManyField('Node', related_name='nodes', blank=True)
                
                num_converted += 1
            
            if time.time() - last_update_time > 1:
                elapsed = time.time() - start
                if elapsed > 0:
                    terms_per_second = i/elapsed
                else:
                    terms_per_second = 0
                
                print 'Converting term %s/%s (%0.1f/s)' % (i, num_terms, terms_per_second)
                last_update_time = time.time()
            
            #if time.time() - start > 3:
            #    break
            
        tags = orm.Node.objects.filter(node_type=tag_type)
        tags2 = {}
        for tag in tags:
            tags2[tag.name] = tag
        
        for i, term in enumerate(terms):
            if term.id in term_id_to_tag_list:
                tag = term_id_to_tag_list[term.id]
                
                for term1 in term.related_terms.all():
                    if term1.name in tags2:
                        tag.related_tags.add(tags2[term1.name])
                    else:
                        # Ignore any missing terms.
                        pass
                tag.save()
            
        print 'num_terms: %s' % num_terms
        print 'num_tags: %s' % num_tags
        print 'num_duplicates: %s' % num_duplicates
        print 'num_converted: %s' % num_converted
        tags = orm.Node.objects.filter(node_type=tag_type)
        print 'num_tags (after): %s' % tags.count()
        print 'num_valid_clusters: %s' % num_valid_clusters
        print 'num_missing_clusters: %s' % num_missing_clusters

    def backwards(self, orm):
        'Removes all Nodes/tags that have is_taxonomy_term True.'
        orm.Node.objects.filter(is_taxonomy_term=True).delete()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ieeetags.failedloginlog': {
            'Meta': {'object_name': 'FailedLoginLog'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '16'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        'ieeetags.filter': {
            'Meta': {'object_name': 'Filter'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'ieeetags.node': {
            'Meta': {'ordering': "['name']", 'object_name': 'Node'},
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'nodes'", 'symmetrical': 'False', 'to': "orm['ieeetags.Filter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_taxonomy_term': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'node_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ieeetags.NodeType']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'child_nodes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['ieeetags.Node']"}),
            'related_tags': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'related_tags_rel_+'", 'null': 'True', 'to': "orm['ieeetags.Node']"}),
            'societies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'tags'", 'blank': 'True', 'to': "orm['ieeetags.Society']"})
        },
        'ieeetags.nodetype': {
            'Meta': {'object_name': 'NodeType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'ieeetags.permission': {
            'Meta': {'object_name': 'Permission'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'object_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['contenttypes.ContentType']"}),
            'permission_type': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'permissions'", 'to': "orm['auth.User']"})
        },
        'ieeetags.processcontrol': {
            'Meta': {'object_name': 'ProcessControl'},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_alive': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'last_processed_tag': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['ieeetags.Node']", 'null': 'True', 'blank': 'True'}),
            'log': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ieeetags.profile': {
            'Meta': {'object_name': 'Profile'},
            'copied_resource': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'copied_users'", 'null': 'True', 'to': "orm['ieeetags.Resource']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_login_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'last_logout_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reset_key': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True'}),
            'role': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'ieeetags.profilelog': {
            'Meta': {'object_name': 'ProfileLog'},
            'category': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'elapsed_time': ('django.db.models.fields.FloatField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'ieeetags.resource': {
            'Meta': {'ordering': "['resource_type__name', 'name']", 'object_name': 'Resource'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'conference_series': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '5000', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ieee_id': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '5000', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'nodes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resources'", 'symmetrical': 'False', 'through': "orm['ieeetags.ResourceNodes']", 'to': "orm['ieeetags.Node']"}),
            'priority_to_tag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'resource_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ieeetags.ResourceType']"}),
            'societies': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resources'", 'symmetrical': 'False', 'to': "orm['ieeetags.Society']"}),
            'standard_status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'url_date_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_error': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'url_status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'ieeetags.resourcenodes': {
            'Meta': {'ordering': "['node__name', 'resource__name']", 'object_name': 'ResourceNodes', 'db_table': "'ieeetags_resource_nodes'"},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_machine_generated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resource_nodes'", 'to': "orm['ieeetags.Node']"}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'resource_nodes'", 'to': "orm['ieeetags.Resource']"})
        },
        'ieeetags.resourcetype': {
            'Meta': {'object_name': 'ResourceType'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'ieeetags.society': {
            'Meta': {'ordering': "['name']", 'object_name': 'Society'},
            'abbreviation': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logo_full': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'logo_thumbnail': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'societies'", 'blank': 'True', 'to': "orm['auth.User']"})
        },
        'ieeetags.taxonomycluster': {
            'Meta': {'object_name': 'TaxonomyCluster'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'ieeetags.taxonomyterm': {
            'Meta': {'object_name': 'TaxonomyTerm'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'related_nodes': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'nodes'", 'blank': 'True', 'to': "orm['ieeetags.Node']"}),
            'related_terms': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'related_terms_rel_+'", 'null': 'True', 'to': "orm['ieeetags.TaxonomyTerm']"}),
            'taxonomy_clusters': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'terms'", 'blank': 'True', 'to': "orm['ieeetags.TaxonomyCluster']"})
        },
        'ieeetags.urlcheckerlog': {
            'Meta': {'object_name': 'UrlCheckerLog'},
            'date_ended': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'date_started': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date_updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        }
    }

    complete_apps = ['ieeetags']
