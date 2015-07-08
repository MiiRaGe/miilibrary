# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='JSONKeyValue',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=40)),
                ('key', models.CharField(max_length=50)),
                ('date', models.DateTimeField()),
                ('value', models.BinaryField()),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='jsonkeyvalue',
            unique_together=set([('type', 'key')]),
        ),
    ]
