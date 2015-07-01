# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0004_auto_20150630_2211'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='movie',
            index_together=set([('year', 'title')]),
        ),
    ]
