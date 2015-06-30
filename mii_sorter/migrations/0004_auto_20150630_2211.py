# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0003_auto_20150622_1556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movie',
            name='title',
            field=models.CharField(max_length=100, db_index=True),
        ),
        migrations.AlterField(
            model_name='movie',
            name='year',
            field=models.IntegerField(default=1900, null=True, db_index=True),
        ),
        migrations.AlterField(
            model_name='whatsnew',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
