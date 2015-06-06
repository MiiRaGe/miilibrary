# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='MovieQuestionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('movie', models.OneToOneField(on_delete=b'CASCADE', to='mii_sorter.Movie')),
            ],
        ),
        migrations.CreateModel(
            name='QuestionAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.FloatField()),
                ('question_type', models.CharField(max_length=50, choices=[(b'actor', b'actor'), (b'story', b'store'), (b'overall', b'overall'), (b'director', b'director')])),
                ('question_set', models.ForeignKey(to='mii_rating.MovieQuestionSet', on_delete=b'CASCADE')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='questionanswer',
            unique_together=set([('question_set', 'question_type')]),
        ),
    ]
