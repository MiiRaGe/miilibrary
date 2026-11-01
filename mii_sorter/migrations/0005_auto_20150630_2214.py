# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0004_auto_20150630_2211'),
    ]

    # Was AlterIndexTogether(('year', 'title')): Django >= 5.1 no longer creates index_together indexes on a fresh
    # database, so removing the previous one failed. The index is managed by 0015.
    operations = [
    ]
