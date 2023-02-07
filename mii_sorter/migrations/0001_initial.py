# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
                ('file_path', models.CharField(max_length=400)),
                ('file_size', models.BigIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=100)),
                ('year', models.IntegerField(default=1900, null=True)),
                ('imdb_id', models.CharField(max_length=15, null=True)),
                ('rating', models.FloatField(null=True)),
                ('folder_path', models.CharField(max_length=400)),
                ('file_size', models.BigIntegerField()),
                ('seen', models.BooleanField(null=True)),
            ],
            options={
                'ordering': ['year', 'title'],
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('number', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='Serie',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='WhatsNew',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateTimeField()),
                ('name', models.CharField(unique=True, max_length=70)),
                ('path', models.CharField(max_length=400)),
            ],
            options={
                'ordering': ['date'],
            },
        ),
        migrations.AddField(
            model_name='season',
            name='serie',
            field=models.ForeignKey(related_name='seasons', on_delete=models.CASCADE, to='mii_sorter.Serie'),
        ),
        migrations.AlterIndexTogether(
            name='movie',
            index_together=set([('title', 'year')]),
        ),
        migrations.AddField(
            model_name='episode',
            name='season',
            field=models.ForeignKey(related_name='episodes', on_delete=models.CASCADE, to='mii_sorter.Season'),
        ),
    ]
