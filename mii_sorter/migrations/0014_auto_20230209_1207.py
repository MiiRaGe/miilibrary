# Generated by Django 4.1.6 on 2023-02-09 12:07
import os

from django.db import migrations
from django.conf import settings

def add_folder_to_serie_and_season(apps, schema_editor):
    Serie = apps.get_model('mii_sorter', 'Serie')
    root_folder = os.path.join(settings.DESTINATION_PLACEHOLDER, 'Series')
    series = Serie.objects.all().prefetch_related('seasons')
    for serie in series:
        serie_path = os.path.join(root_folder, serie.name)
        serie.folder_path = serie_path
        serie.save()

        for season in serie.seasons.all():
            season.folder_path = os.path.join(serie_path, 'Season %s' % season.number)
            season.save()

class Migration(migrations.Migration):

    dependencies = [
        ('mii_sorter', '0013_season_folder_path_serie_folder_path'),
    ]

    operations = [
        migrations.RunPython(add_folder_to_serie_and_season)
    ]
