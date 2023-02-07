# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from datetime import timezone


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField(default=datetime.datetime(2015, 6, 22, 21, 5, 32, 770241, tzinfo=timezone.utc), db_index=True)),
                ('report_type', models.CharField(max_length=50, db_index=True)),
                ('report_html', models.TextField()),
            ],
        ),
    ]
