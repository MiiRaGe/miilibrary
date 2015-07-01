# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('mii_rss', '0002_feedentries'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feedentries',
            name='date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
