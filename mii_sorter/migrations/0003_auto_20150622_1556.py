# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0002_auto_20150606_0922'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='episode',
            options={'ordering': ('season__serie__name', 'season__number', 'number')},
        ),
        migrations.AlterModelOptions(
            name='season',
            options={'ordering': ('serie__name', 'number')},
        ),
    ]
