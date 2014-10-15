# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        for abbr in ['NPS', 'PHOT', 'SP', 'TAB']:
            soc = orm.Society.objects.get(abbreviation=abbr)
            soc.logo_full = 'images/sc_logos/full/%s.jpg' % abbr
            soc.logo_thumbnail = 'images/sc_logos/thumbnail/%s.jpg' % abbr
            soc.save()
        
    def backwards(self, orm):
        "Write your backwards methods here."


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '80', 'unique': 'True'}),
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
            'username': ('django.db.models.fields.CharField', [], {'max_length': '30', 'unique': 'True'})
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
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'child_nodes'", 'blank': 'True', 'null': 'True', 'to': "orm['ieeetags.Node']"}),
            'related_tags': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_tags_rel_+'", 'blank': 'True', 'null': 'True', 'to': "orm['ieeetags.Node']"}),
            'societies': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'tags'", 'blank': 'True', 'through': "orm['ieeetags.NodeSocieties']", 'to': "orm['ieeetags.Society']"})
        },
        'ieeetags.nodesocieties': {
            'Meta': {'ordering': "['node__name', 'society__name']", 'object_name': 'NodeSocieties', 'db_table': "'ieeetags_node_societies'"},
            'date_created': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_machine_generated': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'node_societies'", 'to': "orm['ieeetags.Node']"}),
            'society': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'node_societies'", 'to': "orm['ieeetags.Society']"})
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
            'log_filename': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '1000', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'ieeetags.profile': {
            'Meta': {'object_name': 'Profile'},
            'copied_resource': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'copied_users'", 'blank': 'True', 'null': 'True', 'to': "orm['ieeetags.Resource']"}),
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
            'pub_id': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
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
            'related_terms': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'related_terms_rel_+'", 'blank': 'True', 'null': 'True', 'to': "orm['ieeetags.TaxonomyTerm']"}),
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
