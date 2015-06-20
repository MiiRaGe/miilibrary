# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_unpacker', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unpacked',
            name='filename',
            field=models.CharField(unique=True, max_length=b'255'),
        ),
    ]
