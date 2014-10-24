# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cache',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('params', models.CharField(max_length=1000, blank=True)),
                ('content', models.TextField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ieeetags_cache',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ConferenceApplication',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200, verbose_name=b'Conference name')),
            ],
            options={
                'db_table': 'ieeetags_conferenceapplication',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='FailedLoginLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('username', models.CharField(max_length=30)),
                ('ip', models.CharField(max_length=16)),
                ('disabled', models.BooleanField(default=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ieeetags_failedloginlog',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
                ('value', models.CharField(max_length=500)),
            ],
            options={
                'db_table': 'ieeetags_filter',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Node',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(max_length=500)),
                ('is_taxonomy_term', models.BooleanField(default=False)),
                ('high_potency', models.BooleanField(default=False)),
                ('definition', models.CharField(max_length=2000, null=True, blank=True)),
                ('definition_source', models.CharField(max_length=50, null=True, blank=True)),
                ('definition_updated_when', models.DateTimeField(null=True, blank=True)),
                ('filters', models.ManyToManyField(related_name=b'nodes', to='webapp.Filter')),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'ieeetags_node',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NodeSocieties',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(default=None, null=True, blank=True)),
                ('is_machine_generated', models.BooleanField(default=False)),
                ('node', models.ForeignKey(related_name=b'node_societies', to='webapp.Node')),
            ],
            options={
                'ordering': ['node__name', 'society__name'],
                'db_table': 'ieeetags_node_societies',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'ieeetags_nodetype',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('permission_type', models.CharField(max_length=1000)),
                ('object_type', models.ForeignKey(related_name=b'permissions', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name=b'permissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ieeetags_permission',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProcessControl',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=100, choices=[(b'XPLORE_IMPORT', b'XPLORE_IMPORT')])),
                ('log', models.CharField(max_length=1000, blank=True)),
                ('log_filename', models.CharField(default=b'', max_length=1000, blank=True)),
                ('is_alive', models.BooleanField(default=True)),
                ('date_updated', models.DateTimeField(null=True, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('last_processed_tag', models.ForeignKey(default=None, blank=True, to='webapp.Node', null=True)),
            ],
            options={
                'db_table': 'ieeetags_processcontrol',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('role', models.CharField(max_length=1000, choices=[(b'admin', b'admin'), (b'society_admin', b'society_admin'), (b'society_manager', b'society_manager'), (b'end_user', b'end_user')])),
                ('reset_key', models.CharField(max_length=1000, null=True)),
                ('last_login_time', models.DateTimeField(null=True, blank=True)),
                ('last_logout_time', models.DateTimeField(null=True, blank=True)),
            ],
            options={
                'db_table': 'ieeetags_profile',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProfileLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.CharField(max_length=1000)),
                ('elapsed_time', models.FloatField()),
                ('user_agent', models.CharField(max_length=1000)),
                ('category', models.CharField(max_length=100, blank=True)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ieeetags_profilelog',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('ieee_id', models.CharField(max_length=500, null=True, blank=True)),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=5000, blank=True)),
                ('url', models.CharField(max_length=1000, blank=True)),
                ('year', models.IntegerField(null=True, blank=True)),
                ('standard_status', models.CharField(max_length=100, blank=True)),
                ('priority_to_tag', models.BooleanField(default=False)),
                ('completed', models.BooleanField(default=False)),
                ('keywords', models.CharField(max_length=5000, blank=True)),
                ('conference_series', models.CharField(max_length=100, blank=True)),
                ('date', models.DateField(null=True, blank=True)),
                ('date_end', models.DateField(null=True, blank=True)),
                ('city', models.CharField(max_length=50, null=True, blank=True)),
                ('state_province', models.CharField(max_length=50, null=True, blank=True)),
                ('country', models.CharField(max_length=50, null=True, blank=True)),
                ('pub_id', models.CharField(max_length=1000, blank=True)),
                ('url_status', models.CharField(blank=True, max_length=100, choices=[(b'good', b'Good'), (b'bad', b'Bad')])),
                ('url_date_checked', models.DateTimeField(null=True, blank=True)),
                ('url_error', models.CharField(max_length=1000, null=True, blank=True)),
            ],
            options={
                'ordering': ['resource_type__name', 'name'],
                'db_table': 'ieeetags_resource',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceAdditionNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_notified', models.DateTimeField()),
            ],
            options={
                'db_table': 'ieeetags_resourceadditionnotification',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceAdditionNotificationRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField()),
                ('email', models.CharField(max_length=255)),
                ('node', models.ForeignKey(related_name=b'notification_node', to='webapp.Node')),
            ],
            options={
                'db_table': 'ieeetags_resourceadditionnotificationrequest',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceNodes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_created', models.DateTimeField(default=None, null=True, blank=True)),
                ('is_machine_generated', models.BooleanField(default=False)),
                ('node', models.ForeignKey(related_name=b'resource_nodes', to='webapp.Node')),
                ('resource', models.ForeignKey(related_name=b'resource_nodes', to='webapp.Resource')),
            ],
            options={
                'ordering': ['node__name', 'resource__name'],
                'db_table': 'ieeetags_resource_nodes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ResourceType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'db_table': 'ieeetags_resourcetype',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Society',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=500)),
                ('description', models.CharField(max_length=5000, blank=True)),
                ('abbreviation', models.CharField(max_length=20)),
                ('url', models.CharField(max_length=1000, blank=True)),
                ('logo_thumbnail', models.FileField(upload_to=b'images/sc_logos/thumbnail', blank=True)),
                ('logo_full', models.FileField(upload_to=b'images/sc_logos/full', blank=True)),
                ('users', models.ManyToManyField(related_name=b'societies', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'ordering': ['name'],
                'db_table': 'ieeetags_society',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TagKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=500)),
                ('tag', models.ForeignKey(to='webapp.Node', null=True)),
            ],
            options={
                'db_table': 'ieeetags_tagkeyword',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaxonomyCluster',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=500)),
            ],
            options={
                'db_table': 'ieeetags_taxonomycluster',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TaxonomyTerm',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=500)),
                ('related_nodes', models.ManyToManyField(related_name=b'nodes', to='webapp.Node', blank=True)),
                ('related_terms', models.ManyToManyField(related_name='related_terms_rel_+', null=True, to='webapp.TaxonomyTerm', blank=True)),
                ('taxonomy_clusters', models.ManyToManyField(related_name=b'terms', to='webapp.TaxonomyCluster', blank=True)),
            ],
            options={
                'db_table': 'ieeetags_taxonomyterm',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UrlCheckerLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_started', models.DateTimeField(auto_now_add=True)),
                ('date_ended', models.DateTimeField(null=True, blank=True)),
                ('date_updated', models.DateTimeField(auto_now=True)),
                ('status', models.CharField(max_length=1000)),
            ],
            options={
                'db_table': 'ieeetags_urlcheckerlog',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='resourceadditionnotificationrequest',
            unique_together=set([('node', 'email')]),
        ),
        migrations.AddField(
            model_name='resourceadditionnotification',
            name='request',
            field=models.ForeignKey(to='webapp.ResourceAdditionNotificationRequest'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceadditionnotification',
            name='resourceNodes',
            field=models.ForeignKey(to='webapp.ResourceNodes', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resourceadditionnotification',
            name='resourceSocieties',
            field=models.ForeignKey(to='webapp.NodeSocieties', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='nodes',
            field=models.ManyToManyField(related_name=b'resources', through='webapp.ResourceNodes', to='webapp.Node'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='resource_type',
            field=models.ForeignKey(to='webapp.ResourceType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='resource',
            name='societies',
            field=models.ManyToManyField(related_name=b'resources', to='webapp.Society'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='copied_resource',
            field=models.ForeignKey(related_name=b'copied_users', blank=True, to='webapp.Resource', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='profile',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, unique=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='nodesocieties',
            name='society',
            field=models.ForeignKey(related_name=b'node_societies', to='webapp.Society'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='node',
            name='node_type',
            field=models.ForeignKey(to='webapp.NodeType'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='node',
            name='parents',
            field=models.ManyToManyField(related_name=b'child_nodes', null=True, to='webapp.Node', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='node',
            name='related_tags',
            field=models.ManyToManyField(related_name='related_tags_rel_+', null=True, to='webapp.Node', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='node',
            name='societies',
            field=models.ManyToManyField(related_name=b'tags', through='webapp.NodeSocieties', to='webapp.Society', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='conferenceapplication',
            name='keywords',
            field=models.ManyToManyField(related_name=b'conference_applications', to='webapp.TagKeyword'),
            preserve_default=True,
        ),
    ]
