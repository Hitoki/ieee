# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'NodeType'
        db.create_table('ieeetags_nodetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('ieeetags', ['NodeType'])

        # Adding model 'Node'
        db.create_table('ieeetags_node', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('node_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ieeetags.NodeType'])),
        ))
        db.send_create_signal('ieeetags', ['Node'])

        # Adding M2M table for field parents on 'Node'
        db.create_table('ieeetags_node_parents', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_node', models.ForeignKey(orm['ieeetags.node'], null=False)),
            ('to_node', models.ForeignKey(orm['ieeetags.node'], null=False))
        ))
        db.create_unique('ieeetags_node_parents', ['from_node_id', 'to_node_id'])

        # Adding M2M table for field societies on 'Node'
        db.create_table('ieeetags_node_societies', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('node', models.ForeignKey(orm['ieeetags.node'], null=False)),
            ('society', models.ForeignKey(orm['ieeetags.society'], null=False))
        ))
        db.create_unique('ieeetags_node_societies', ['node_id', 'society_id'])

        # Adding M2M table for field filters on 'Node'
        db.create_table('ieeetags_node_filters', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('node', models.ForeignKey(orm['ieeetags.node'], null=False)),
            ('filter', models.ForeignKey(orm['ieeetags.filter'], null=False))
        ))
        db.create_unique('ieeetags_node_filters', ['node_id', 'filter_id'])

        # Adding M2M table for field related_tags on 'Node'
        db.create_table('ieeetags_node_related_tags', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_node', models.ForeignKey(orm['ieeetags.node'], null=False)),
            ('to_node', models.ForeignKey(orm['ieeetags.node'], null=False))
        ))
        db.create_unique('ieeetags_node_related_tags', ['from_node_id', 'to_node_id'])

        # Adding model 'Society'
        db.create_table('ieeetags_society', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('abbreviation', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('logo_thumbnail', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
            ('logo_full', self.gf('django.db.models.fields.files.FileField')(max_length=100, blank=True)),
        ))
        db.send_create_signal('ieeetags', ['Society'])

        # Adding M2M table for field users on 'Society'
        db.create_table('ieeetags_society_users', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('society', models.ForeignKey(orm['ieeetags.society'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('ieeetags_society_users', ['society_id', 'user_id'])

        # Adding model 'ResourceType'
        db.create_table('ieeetags_resourcetype', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
        ))
        db.send_create_signal('ieeetags', ['ResourceType'])

        # Adding model 'Resource'
        db.create_table('ieeetags_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ieeetags.ResourceType'])),
            ('ieee_id', self.gf('django.db.models.fields.CharField')(max_length=500, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=5000, blank=True)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=1000, blank=True)),
            ('year', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('standard_status', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('priority_to_tag', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=5000, blank=True)),
            ('conference_series', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('url_status', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('url_date_checked', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('url_error', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True, blank=True)),
        ))
        db.send_create_signal('ieeetags', ['Resource'])

        # Adding M2M table for field nodes on 'Resource'
        db.create_table('ieeetags_resource_nodes', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resource', models.ForeignKey(orm['ieeetags.resource'], null=False)),
            ('node', models.ForeignKey(orm['ieeetags.node'], null=False))
        ))
        db.create_unique('ieeetags_resource_nodes', ['resource_id', 'node_id'])

        # Adding M2M table for field societies on 'Resource'
        db.create_table('ieeetags_resource_societies', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('resource', models.ForeignKey(orm['ieeetags.resource'], null=False)),
            ('society', models.ForeignKey(orm['ieeetags.society'], null=False))
        ))
        db.create_unique('ieeetags_resource_societies', ['resource_id', 'society_id'])

        # Adding model 'Filter'
        db.create_table('ieeetags_filter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=500)),
        ))
        db.send_create_signal('ieeetags', ['Filter'])

        # Adding model 'Permission'
        db.create_table('ieeetags_permission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['auth.User'])),
            ('object_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='permissions', to=orm['contenttypes.ContentType'])),
            ('object_id', self.gf('django.db.models.fields.PositiveIntegerField')()),
            ('permission_type', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('ieeetags', ['Permission'])

        # Adding model 'Profile'
        db.create_table('ieeetags_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('role', self.gf('django.db.models.fields.CharField')(max_length=1000)),
            ('reset_key', self.gf('django.db.models.fields.CharField')(max_length=1000, null=True)),
            ('last_login_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('last_logout_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('copied_resource', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='copied_users', null=True, to=orm['ieeetags.Resource'])),
        ))
        db.send_create_signal('ieeetags', ['Profile'])

        # Adding model 'FailedLoginLog'
        db.create_table('ieeetags_failedloginlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('ip', self.gf('django.db.models.fields.CharField')(max_length=16)),
            ('disabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date_created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('ieeetags', ['FailedLoginLog'])

        # Adding model 'UrlCheckerLog'
        db.create_table('ieeetags_urlcheckerlog', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date_started', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('date_ended', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('date_updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('ieeetags', ['UrlCheckerLog'])


    def backwards(self, orm):
        
        # Deleting model 'NodeType'
        db.delete_table('ieeetags_nodetype')

        # Deleting model 'Node'
        db.delete_table('ieeetags_node')

        # Removing M2M table for field parents on 'Node'
        db.delete_table('ieeetags_node_parents')

        # Removing M2M table for field societies on 'Node'
        db.delete_table('ieeetags_node_societies')

        # Removing M2M table for field filters on 'Node'
        db.delete_table('ieeetags_node_filters')

        # Removing M2M table for field related_tags on 'Node'
        db.delete_table('ieeetags_node_related_tags')

        # Deleting model 'Society'
        db.delete_table('ieeetags_society')

        # Removing M2M table for field users on 'Society'
        db.delete_table('ieeetags_society_users')

        # Deleting model 'ResourceType'
        db.delete_table('ieeetags_resourcetype')

        # Deleting model 'Resource'
        db.delete_table('ieeetags_resource')

        # Removing M2M table for field nodes on 'Resource'
        db.delete_table('ieeetags_resource_nodes')

        # Removing M2M table for field societies on 'Resource'
        db.delete_table('ieeetags_resource_societies')

        # Deleting model 'Filter'
        db.delete_table('ieeetags_filter')

        # Deleting model 'Permission'
        db.delete_table('ieeetags_permission')

        # Deleting model 'Profile'
        db.delete_table('ieeetags_profile')

        # Deleting model 'FailedLoginLog'
        db.delete_table('ieeetags_failedloginlog')

        # Deleting model 'UrlCheckerLog'
        db.delete_table('ieeetags_urlcheckerlog')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
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
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
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
            'filters': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'nodes'", 'to': "orm['ieeetags.Filter']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'node_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ieeetags.NodeType']"}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'child_nodes'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['ieeetags.Node']"}),
            'related_tags': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'related_tags_rel_+'", 'null': 'True', 'to': "orm['ieeetags.Node']"}),
            'societies': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'tags'", 'blank': 'True', 'to': "orm['ieeetags.Society']"})
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
            'nodes': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resources'", 'to': "orm['ieeetags.Node']"}),
            'priority_to_tag': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'resource_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['ieeetags.ResourceType']"}),
            'societies': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'resources'", 'to': "orm['ieeetags.Society']"}),
            'standard_status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'blank': 'True'}),
            'url_date_checked': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'url_error': ('django.db.models.fields.CharField', [], {'max_length': '1000', 'null': 'True', 'blank': 'True'}),
            'url_status': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'year': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
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
            'users': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'societies'", 'blank': 'True', 'to': "orm['auth.User']"})
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
