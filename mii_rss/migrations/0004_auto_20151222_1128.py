# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2015-12-22 11:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mii_rss', '0003_auto_20150630_2211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='feeddownloaded',
            name='episode',
            field=models.IntegerField(null=True),
        ),
    ]