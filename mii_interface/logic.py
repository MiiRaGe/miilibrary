import logging
import os
import re

from django.conf import settings
from pyreport.reporter import Report

from mii_common import tools
from mii_sorter.models import Movie, Serie, Season, Episode, insert_report

logger = logging.getLogger(__name__)

if settings.REPORT_ENABLED:
    logger = Report()


def check_library():
    """
    Periodic check of the library structure on the filesystem worker: fixes the discrepancies and reports them.
    """
    if settings.REPORT_ENABLED:
        logger.create_report()
    logger.info(u'****************************************')
    logger.info(u'**********   Library check    **********')
    logger.info(u'****************************************')
    for discrepancy_type, discrepancies in fix_discrepancies().items():
        for discrepancy in discrepancies:
            logger.info(u'Fixed %s: %s' % (discrepancy_type, discrepancy))
    if settings.REPORT_ENABLED:
        insert_report(logger.finalize_report(), report_type='library_check')


def find_discrepancies():
    """
    Compares the state of the db and filesystem and returns the discrepancies.
    Must run where the library is mounted (the filesystem worker), every path would look missing otherwise.
    """
    tools.check_mounted(os.path.join(settings.DESTINATION_FOLDER, 'Movies', 'All'))

    movie_discrepancy = []
    folder_discrepancy = []
    series_discrepancy = []
    seasons_discrepancy = []
    episodes_discrepancy = []
    serie_folder_discrepancy = []

    movies = Movie.objects.all()
    for movie in movies:
        if not os.path.exists(movie.abs_folder_path):
            movie_discrepancy.append({'title': movie.title, 'id': movie.id})
    
    episodes = Episode.objects.all().select_related('season','season__serie')
    for episode in episodes:
        if not os.path.exists(episode.abs_file_path):
            episodes_discrepancy.append({'title': str(episode), 'file_path': episode.file_path, 'id': episode.id})
    
    seasons = Season.objects.all().select_related('serie').prefetch_related('episodes')
    for season in seasons:
        if list(season.episodes.all()) == []:
            seasons_discrepancy.append({'number': str(season.number), 'id': season.id})
    
    series = Serie.objects.all().prefetch_related('seasons')
    for serie in series:
        if list(serie.seasons.all()) == []:
            series_discrepancy.append({'name': str(serie.name), 'id': serie.id})  

    compiled_re = re.compile(r'^(.+) \((\d{4})\).*$')
    folder_dir = os.path.join(settings.DESTINATION_FOLDER, 'Movies', 'All')
    try:
        for movie_folder in os.listdir(folder_dir):
            movie_path = os.path.join(folder_dir, movie_folder)
            matched_info = compiled_re.match(movie_folder)
            if not matched_info:
                folder_discrepancy.append({'folder': movie_path, 'error': matched_info})
                continue
            title = matched_info.group(1)
            year = matched_info.group(2)
            movie_object = Movie.objects.filter(title=title, year=year).first()
            if not movie_object:
                folder_discrepancy.append({'folder': movie_path})
            elif movie_object.abs_folder_path != movie_path:
                folder_discrepancy.append({'folder': movie_path,
                                        'folder_exists': os.path.exists(movie_path),
                                        'movie_id': movie_object.id,
                                        'movie_folder': movie_object.abs_folder_path,
                                        'movie_folder_exists': os.path.exists(movie_object.abs_folder_path)})

        # {
        # 'name': 'serie1'
        # 'seasons': [
        #   {
        #    'number': 1,
        #    'episodes': [
        #    'number': 1
        #    'file_path': '//',
        #    'file_size': 1,
        #    ]
        #   }
        # ]
        # }
        serie_folder_dir = os.path.join(settings.DESTINATION_FOLDER, 'TVSeries')
        season_re = re.compile(r'\ASeason (\d+)\Z')
        for serie_folder in os.listdir(serie_folder_dir):
            serie_path = os.path.join(serie_folder_dir, serie_folder)
            serie_object = Serie.objects.filter(name=serie_folder).prefetch_related('seasons', 'seasons__episodes').first()
            discrepancy = {
                'name': serie_folder,
                'folder_path': serie_path,
                'seasons': [],
            }
            if not serie_object:   
                for season_folder in os.listdir(serie_path):
                    result = season_re.match(season_folder)
                    if not result:
                        continue
                    season_path = os.path.join(serie_path, season_folder)
                    season_discrepancy = {
                        'number': result.group(1),
                        'folder_path': season_path,
                        'episodes': [],
                    }
                    discrepancy['seasons'].append(season_discrepancy)
                    for episode in os.listdir(season_path):
                        serie_regex = re.compile(r'\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
                        result = serie_regex.match(episode)
                        if result:
                            episode_path = os.path.join(season_path, episode)
                            season_discrepancy['episodes'].append({
                                'number': int(result.group(1)),
                                'file_path': episode_path,
                                'file_size': os.path.getsize(episode_path),
                            })
                serie_folder_discrepancy.append(discrepancy)
            else:
                for season_folder in os.listdir(serie_path):
                    result = season_re.match(season_folder)
                    if not result:
                        continue
                    season_path = os.path.join(serie_path, season_folder)
                    season_object = serie_object.seasons.filter(number=result.group(1)).first()
                    season_discrepancy = {
                        'number': result.group(1),
                        'folder_path': season_path,
                        'episodes': [],
                        }
                    if not season_object:
                        discrepancy['seasons'].append(season_discrepancy)
                        for episode in os.listdir(season_path):
                            serie_regex = re.compile(r'\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
                            result = serie_regex.match(episode)
                            if result:
                                episode_path = os.path.join(season_path, episode)
                                season_discrepancy['episodes'].append({
                                    'number': int(result.group(1)),
                                    'file_path': episode_path,
                                    'file_size': os.path.getsize(episode_path),
                                })
                    else:
                        for episode in os.listdir(season_path):
                            serie_regex = re.compile(r'\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
                            result = serie_regex.match(episode)
                            if result:
                                episode_object = season_object.episodes.filter(number=result.group(1)).first()
                                if not episode_object:
                                    episode_path = os.path.join(season_path, episode)
                                    season_discrepancy['episodes'].append({
                                        'number': int(result.group(1)),
                                        'file_path': episode_path,
                                        'file_size': os.path.getsize(episode_path),
                                    })
                        if season_discrepancy['episodes'] != []:
                            discrepancy['seasons'].append(season_discrepancy)
                if discrepancy['seasons'] != []:
                    serie_folder_discrepancy.append(discrepancy)
    except FileNotFoundError:
        pass

    return {'movie_discrepancy': sorted(movie_discrepancy, key=lambda x: x['title']),
            'folder_discrepancy': sorted(folder_discrepancy, key=lambda x: x['folder']),
            'series_discrepancy': sorted(series_discrepancy, key=lambda x: x['name']),
            'seasons_discrepancy': sorted(seasons_discrepancy, key=lambda x: x['number']),
            'episodes_discrepancy': sorted(episodes_discrepancy, key=lambda x: x['title']),
            'serie_folder_discrepancy': sorted(serie_folder_discrepancy, key=lambda x: x['name']),
            }


def fix_discrepancies():
    """
    Fixes the discrepancies found by find_discrepancies, removing db entries with no files and moving orphan
    folders back to the data folder to be sorted again.
    """
    discrepancies = find_discrepancies()
    movie_discrepancy = discrepancies['movie_discrepancy']
    folder_discrepancy = discrepancies['folder_discrepancy']
    episodes_discrepancy = discrepancies['episodes_discrepancy']
    serie_folder_discrepancy = discrepancies['serie_folder_discrepancy']
    Movie.objects.filter(id__in=[x['id'] for x in movie_discrepancy]).delete()
    media_dir = os.path.join(settings.DESTINATION_FOLDER, 'data')
    for discrepancy in folder_discrepancy:
        if not discrepancy.get('movie_folder'):
            for dirpath, dirnames, filenames in os.walk(discrepancy.get('folder')):
                for filename in filenames:
                    os.rename(os.path.join(dirpath, filename), os.path.join(media_dir, filename))
                    if os.path.exists(os.path.join(dirpath, filename)):
                        raise Exception('Stopping because file wasn\'t deleted')
            tools.delete_dir(discrepancy.get('folder'))
        else:
            if discrepancy['movie_folder_exists']:
                for dirpath, dirnames, filenames in os.walk(discrepancy['movie_folder']):
                    for filename in filenames:
                        os.rename(os.path.join(dirpath, filename), os.path.join(media_dir, filename))
                        if os.path.exists(os.path.join(dirpath, filename)):
                            raise Exception('Stopping because file wasn\'t deleted')
                tools.delete_dir(discrepancy['movie_folder'])
            movie = Movie.objects.get(id=discrepancy['movie_id'])
            movie.folder_path = discrepancy['folder']
            movie.save()

    Episode.objects.filter(id__in=[x['id'] for x in episodes_discrepancy]).delete()
    for season in Season.objects.all().prefetch_related('episodes'):
        if len(season.episodes.all()) == 0:
            season.delete()
    for serie in Serie.objects.all().prefetch_related('seasons'):
        if len(serie.seasons.all()) == 0:
            serie.delete()

    for discrepancy in serie_folder_discrepancy:
        serie, _ = Serie.objects.get_or_create(name=discrepancy['name'])
        serie.folder_path = discrepancy['folder_path']
        serie.save()
        for season_discrepancy in discrepancy['seasons']:
            season, _ = Season.objects.get_or_create(serie=serie, number=season_discrepancy['number'])
            season.folder_path = season_discrepancy['folder_path']
            season.save()

            for episode_discrepancy in season_discrepancy['episodes']:
                episode, _ = Episode.objects.get_or_create(season=season, number=episode_discrepancy['number'], defaults={'file_size': 5})
                episode.file_path = episode_discrepancy['file_path']
                episode.file_size = episode_discrepancy['file_size']
                episode.save()
    return discrepancies
