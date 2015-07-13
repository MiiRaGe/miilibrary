# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0006_auto_20150630_2220'),
    ]

    operations = [
        migrations.AddField(
            model_name='movie',
            name='indexed',
            field=models.BooleanField(default=False),
        ),
    ]
