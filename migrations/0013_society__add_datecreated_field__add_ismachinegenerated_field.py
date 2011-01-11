# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        db.add_column('ieeetags_node_societies', 'date_created', models.DateTimeField(blank=True, null=True, default=None))
        db.add_column('ieeetags_node_societies', 'is_machine_generated', models.BooleanField(default=False))

    def backwards(self, orm):
        db.delete_column('ieeetags_node_societies', 'date_created')
        db.delete_column('ieeetags_node_societies', 'is_machine_generated')

