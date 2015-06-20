# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovieRelation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.CharField(max_length=10)),
                ('movie', models.ForeignKey(to='mii_sorter.Movie')),
            ],
        ),
        migrations.CreateModel(
            name='MovieTagging',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('movie', models.ForeignKey(to='mii_sorter.Movie')),
            ],
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
        ),
        migrations.CreateModel(
            name='Tag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=50)),
            ],
        ),
        migrations.AddField(
            model_name='movietagging',
            name='tag',
            field=models.ForeignKey(to='mii_indexer.Tag'),
        ),
        migrations.AddField(
            model_name='movierelation',
            name='person',
            field=models.ForeignKey(to='mii_indexer.Person'),
        ),
        migrations.AlterUniqueTogether(
            name='movietagging',
            unique_together=set([('movie', 'tag')]),
        ),
        migrations.AlterUniqueTogether(
            name='movierelation',
            unique_together=set([('movie', 'person', 'type')]),
        ),
    ]
