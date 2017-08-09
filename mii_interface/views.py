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
from mii_sorter.models import Movie, Serie, Episode
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
    movies = Movie.objects.all()
    movie_discrepancy = []
    for movie in movies:
        if not os.path.exists(movie.abs_folder_path):
            movie_discrepancy.append({'title': movie.title, 'id': movie.id})

    folder_discrepancy = []
    compiled_re = re.compile(u'^(.+) \((\d{4})\).*$')
    folder_dir = os.path.join(settings.DESTINATION_FOLDER, 'Movies', 'All')
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
        return redirect('discrepancies')
    return render(request,
                  'mii_interface/discrepancies.html',
                  {'movie_discrepancy': sorted(movie_discrepancy, key=lambda x: x['title']),
                   'folder_discrepancy': sorted(folder_discrepancy, key=lambda x: x['folder'])})


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
