# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='serie',
            name='name',
            field=models.CharField(unique=True, max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='episode',
            unique_together=set([('number', 'season')]),
        ),
        migrations.AlterUniqueTogether(
            name='season',
            unique_together=set([('number', 'serie')]),
        ),
    ]
