# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

#from ieeetags.util import update_conference_series_tags
import time

def update_conference_series_tags(orm, conferences=None, conference_series=None):
    '''
    Updates conferences so that each future conference inherits all previous years' conferences' tags.
    Must give either conferences or conference_series.
    @param conferences A list of conferences to update, should be sorted by conference_series, then year.  All conferences should have a valid conference_series value, and a valid year value.
    @param conference_series (string) A series to parse through. Will grab all conferences of this series and update them.
    '''
    #from models import Resource, ResourceNodes, ResourceType
    if conferences is not None and conference_series is None:
        pass
    elif conferences is None and conference_series is not None:
        conference_type = orm.ResourceType.objects.getFromName(orm.ResourceType.CONFERENCE)
        conferences = orm.Resource.objects.filter(resource_type=conference_type, conference_series=conference_series).exclude(year__isnull=True).order_by('year')
    else:
        raise Exception('Both conferences (%r) and conference_series (%r) were specified, should only specify one.' % (conferences, conference_series))
    
    num_conferences = 0
    num_series = 0
    num_tags_added = 0
    
    num_total_conferences = conferences.count()
    
    series = ''
    last_update_time = None
    start = time.time()
    for i, conference in enumerate(conferences):
        assert conference.conference_series.strip() != ''
        assert conference.year is not None
        assert conference.year != 0
        
        if series != conference.conference_series:
            # Start of a new series.
            tags = []
            series = conference.conference_series
            num_series += 1
            #print '' 
        
        tags1 = [tag.name for tag in conference.nodes.all()]
        num_tags1 = conference.nodes.count()
        
        # Add all previous tags to this conference.
        for tag in tags:
            if tag not in conference.nodes.all():
                resource_nodes = orm.ResourceNodes()
                resource_nodes.resource = conference
                resource_nodes.node = tag
                resource_nodes.is_machine_generated = True
                resource_nodes.save()
        
        # Add all of this conference's tags to the list.
        for tag in conference.nodes.all():
            if tag not in tags:
                tags.append(tag)
                num_tags_added += 1
        conference.save()
        
        tags2 = [tag.name for tag in conference.nodes.all()]
        num_tags2 = conference.nodes.count()
        
        #print 'conference: %s, %s, %s, %s' % (conference.id, conference.conference_series, conference.year, conference.name)
        #print '  %s' % (','.join(tags1))
        #print '  %s' % (','.join(tags2))
        
        num_conferences += 1
        
        if not last_update_time or time.time() - last_update_time > 1:
            try:
                print('    Parsing row %d/%d, row/sec %f' % (i, num_total_conferences, i/(time.time()-start) ))
            except Exception:
                pass
            last_update_time = time.time()
    
    return {
        'num_conferences': num_conferences,
        'num_series': num_series,
        'num_tags_added': num_tags_added,
    }

class Migration(DataMigration):

    def forwards(self, orm):
        "Copies tags for conferences in each series to all future conferences in the series."
        
        conference_type = orm.ResourceType.objects.get(name='conference')
        conferences = orm.Resource.objects.filter(resource_type=conference_type).exclude(conference_series='').exclude(year__isnull=True).order_by('conference_series', 'year')
        
        results = update_conference_series_tags(orm, conferences=conferences)
        
        print 'Results:'
        print '  num_conferences: %s' % results['num_conferences']
        print '  num_series: %s' % results['num_series']
        print '  num_tags_added: %s' % results['num_tags_added']
        
    def backwards(self, orm):
        ""
        pass

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
