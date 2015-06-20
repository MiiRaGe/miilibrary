# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FeedDownloaded',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('season', models.IntegerField()),
                ('episode', models.IntegerField()),
                ('re_filter', models.CharField(max_length=100)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='feeddownloaded',
            unique_together=set([('season', 'episode', 're_filter')]),
        ),
    ]
