import json
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse

from django.shortcuts import render

from mii_indexer.models import MovieTagging, MovieRelation
from mii_interface.models import Report
from mii_sorter.models import Movie, Serie, Episode
from mii_rating.mii_rating import get_questions, save_question_answers, set_movie_unseen
from mii_unpacker.tasks import unpack
from mii_sorter.tasks import sort, rescan_media_streamer
from mii_indexer.tasks import index_movies


def index(request):
    return render(request, 'mii_interface/index.html')


def movies(request):
    return render(request, 'mii_interface/movie.html', dict(movies=Movie.objects.all().values_list('title', 'year', 'rating')))


def series(request):
    serie = Episode.objects.all().select_related('season__number', 'season__serie__name').values()
    return render(request, 'mii_interface/serie.html', dict(series=serie))


def rate(request):
    questions = get_questions()
    movie = Movie.objects.filter(seen=None).order_by('?')[0]

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

    movies_choices_json = json.dumps([{'label': movie_obj['title'], 'value': movie_obj['id']} for movie_obj in Movie.objects.all().values('title', 'id')])
    genres = [x['tag__name'] for x in MovieTagging.objects.filter(movie=movie).values('tag__name')]
    actors = [x['person__name'] for x in MovieRelation.objects.filter(movie=movie, type='Actor').values('person__name')]
    directors = [x['person__name'] for x in MovieRelation.objects.filter(movie=movie, type='Director').values('person__name')]
    return render(request, 'mii_interface/rate.html',
                  dict(questions=questions, movie=movie, movies_choices_json=movies_choices_json,
                       genres=genres, actors=actors, directors=directors))

def reports(request):
    reports = Report.objects.all().order_by('-date')
    return render(request, 'mii_interface/reports.html', {'reports': reports})


def report(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except ObjectDoesNotExist:
        report = None
    return render(request, 'mii_interface/report.html', {'report': report})


def start_unpack_sort_indexer(request):
    (unpack.si() | sort.si() | index_movies.si() | rescan_media_streamer.si() ).delay()
    return HttpResponse('OK, unpack sort index started')