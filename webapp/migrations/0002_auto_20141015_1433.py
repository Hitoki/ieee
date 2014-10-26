# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('webapp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserExternalFavorites',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('external_resource_type', models.CharField(max_length=50)),
                ('external_id', models.CharField(max_length=500)),
                ('title', models.CharField(default=b'Untitled', max_length=500)),
                ('creation_date', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ieeetags_userexternalfavorites',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='UserFavorites',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('resources', models.ManyToManyField(help_text=b'Favorite Resources', related_name=b'user_favorite_resources', to='webapp.Resource', blank=True)),
                ('societies', models.ManyToManyField(help_text=b'Favorite Societies', related_name=b'user_favorite_societies', to='webapp.Society', blank=True)),
                ('topics', models.ManyToManyField(help_text=b'Favorite Topics', related_name=b'user_favorite_topics', to='webapp.Node', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'ieeetags_userfavorites',
            },
            bases=(models.Model,),
        ),
        migrations.AlterField(
            model_name='resourceadditionnotificationrequest',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
