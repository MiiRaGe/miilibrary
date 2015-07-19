# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.conf import settings
from django.db import migrations

from mii_sorter.models import Movie, Episode


def change_folder_path_to_abs(apps, schema_editor):
    for movie in Movie.objects.all():
        folder_path = movie.folder_path.replace(settings.NAS_ROOT, settings.LOCAL_ROOT).replace(settings.DESTINATION_FOLDER, '{destination_folder}')
        movie.folder_path = folder_path
        movie.save()

    for episode in Episode.objects.all():
        file_path = episode.file_path.replace(settings.NAS_ROOT, settings.LOCAL_ROOT).replace(settings.DESTINATION_FOLDER, '{destination_folder}')
        episode.file_path = file_path
        episode.save()

class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0007_movie_indexed'),
    ]

    operations = [
        migrations.RunPython(change_folder_path_to_abs)
    ]
