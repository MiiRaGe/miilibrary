# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from datetime import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mii_rss', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedEntries',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('json_entries', models.TextField()),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 6, 26, 20, 42, 31, 349515, tzinfo=timezone.utc))),
            ],
            options={
                'get_latest_by': 'date',
            },
        ),
    ]
