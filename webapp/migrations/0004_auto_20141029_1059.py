# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0003_auto_20141020_0910'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tagkeyword',
            name='tag',
            field=models.ForeignKey(blank=True, to='webapp.Node', null=True),
            preserve_default=True,
        ),
    ]
