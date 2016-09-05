# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import migrations

from mii_sorter.models import Movie, Episode


def change_folder_path_to_abs(apps, schema_editor):
    for movie in Movie.objects.exclude(folder_path__icontains=settings.DESTINATION_PLACEHOLDER):
        folder_path = movie.folder_path.replace(u'{destination_dir}', settings.DESTINATION_PLACEHOLDER)
        movie.folder_path = folder_path
        movie.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0009_regexrenaming'),
    ]

    operations = [
        migrations.RunPython(change_folder_path_to_abs)
    ]
