import json
import os
import re
from collections import defaultdict

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from middleware.remote_execution import remote_play
from mii_common import tools
from mii_indexer.models import MovieTagging, MovieRelation
from mii_interface.models import Report
from mii_sorter.models import Movie, Serie, Season, Episode
from mii_rating.mii_rating import get_questions, save_question_answers, set_movie_unseen
from mii_unpacker.tasks import unpack
from mii_sorter.tasks import sort
from mii_indexer.tasks import index_movies


def index(request):
    return render(request, 'mii_interface/index.html')


def movies(request):
    return render(request, 'mii_interface/movie.html', dict(movies=Movie.objects.all().values('title', 'year', 'rating',
                                                                                              'imdb_id')))


def series(request):
    episodes = Episode.objects.all().order_by('season__serie__name',
                                              'season__number',
                                              'number').values('id',
                                                               'number',
                                                               'season__number',
                                                               'season__serie__name')
    organised_episodes = defaultdict(lambda: defaultdict(list))
    for episode in episodes:
        organised_episodes[episode['season__serie__name']][episode['season__number']].append(
            (episode['number'], episode['id']))

    for key, value in organised_episodes.items():
        organised_episodes[key] = dict(value)

    return render(request, 'mii_interface/serie.html',
                  dict(series=sorted(dict(organised_episodes).items(), key=lambda x: x[0])))


def rate(request):
    questions = get_questions()
    try:
        movie = Movie.objects.filter(seen=None).order_by('?')[0]
        genres = [x['tag__name'] for x in MovieTagging.objects.filter(movie=movie).values('tag__name')]
        actors = [x['person__name'] for x in
                  MovieRelation.objects.filter(movie=movie, type='Actor').values('person__name')]
        directors = [x['person__name'] for x in
                     MovieRelation.objects.filter(movie=movie, type='Director').values('person__name')]
    except IndexError:
        movie = None
        genres = None
        actors = None
        directors = None

    if request.method == 'POST':
        data = request.POST
        action = data.get('action')
        if action == 'save_movie':
            save_question_answers(data['movie_id'], question_answers=data)
        elif action == 'not_seen':
            set_movie_unseen(data['movie_id'])

    if request.method == 'GET':
        movie_id = request.GET.get('movie_id')
        try:
            movie = Movie.objects.get(id=movie_id)
        except ObjectDoesNotExist:
            pass

    movies_choices_json = json.dumps([{'label': movie_obj['title'], 'value': movie_obj['id']} for movie_obj in
                                      Movie.objects.all().values('title', 'id')])
    return render(request, 'mii_interface/rate.html',
                  dict(questions=questions, movie=movie, movies_choices_json=movies_choices_json,
                       genres=genres, actors=actors, directors=directors))


def discrepancies(request):
    """
    Compares the state of th db and filesystem, mark discrepancies and fixes them on post
    :param request:
    :return:
    """
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

    compiled_re = re.compile(u'^(.+) \((\d{4})\).*$')
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
        serie_folder_dir = os.path.join(settings.DESTINATION_FOLDER, 'Series')
        season_re = re.compile('\ASeason (\d+)\Z')
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
                        serie_regex = re.compile('\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
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
                            serie_regex = re.compile('\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
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
                            serie_regex = re.compile('\A.*[sS]0*\d+\s?[eE](\d+).*\Z')
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

    if request.method == 'POST':
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

        return redirect('discrepancies')
    return render(request,
                  'mii_interface/discrepancies.html',
                  {'movie_discrepancy': sorted(movie_discrepancy, key=lambda x: x['title']),
                   'folder_discrepancy': sorted(folder_discrepancy, key=lambda x: x['folder']),
                   'series_discrepancy': sorted(series_discrepancy, key=lambda x: x['name']),
                   'seasons_discrepancy': sorted(seasons_discrepancy, key=lambda x: x['number']),
                   'episodes_discrepancy': sorted(episodes_discrepancy, key=lambda x: x['title']),
                   'serie_folder_discrepancy': sorted(serie_folder_discrepancy, key=lambda x: x['name']),
                   })


def reports(request):
    reports = Report.objects.all().order_by('-date')[:50]
    return render(request, 'mii_interface/reports.html', {'reports': reports})


def report(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except ObjectDoesNotExist:
        report = None
    return render(request, 'mii_interface/report.html', {'report': report})


def start_unpack_sort_indexer(request):
    (unpack.si() | sort.si() | index_movies.si()).delay()
    return HttpResponse('OK, unpack sort index started')


@require_POST
def play(request):
    data = request.POST
    if 'episode_id' in data:
        try:
            episode = Episode.objects.get(id=data['episode_id'])
            remote_play(episode.file_path)
        except ObjectDoesNotExist:
            pass
    return redirect('series')
