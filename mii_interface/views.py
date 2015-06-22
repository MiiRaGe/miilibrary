import json
from django.core.exceptions import ObjectDoesNotExist

from django.shortcuts import render

from mii_indexer.models import MovieTagging, MovieRelation
from mii_interface.models import Report
from mii_sorter.models import Movie, Serie
from mii_rating.mii_rating import get_questions, save_question_answers, set_movie_unseen


def index(request):
    return render(request, 'mii_interface/index.html')


def movies(request):
    return render(request, 'mii_interface/movie.html', dict(movies=[x for x in Movie.objects.all()]))


def series(request):
    return render(request, 'mii_interface/serie.html', dict(series=[x for x in Serie.objects.all()]))


def rate(request):
    questions = get_questions()
    movie = Movie.objects.filter(seen=None).order_by('?')[0]

    if request.method == 'POST':
        data = request.form
        action = data.get('action')
        if action == 'save_movie':
            save_question_answers(data['movie_id'], question_answers=data)
        elif action == 'not_seen':
            set_movie_unseen(data['movie_id'])

    if request.method == 'GET':
        movie_id = request.args.get('movie_id')
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            pass

    movies_choices_json = json.dumps([{'label': x.title, 'value': x.id} for x in Movie.select()])
    genres = [x.tag.name for x in MovieTagging.filter(movie=movie)]
    actors = [x.person.name for x in MovieRelation.filter(movie=movie, type='Actor')]
    directors = [x.person.name for x in MovieRelation.filter(movie=movie, type='Director')]
    return render(request, 'mii_interface/rate.html',
                  dict(questions=questions, movie=movie, movies_choices_json=movies_choices_json,
                       genres=genres, actors=actors, directors=directors))


def reports(request):
    reports = Report.objects.all().order_by('date')
    return render(request, 'mii_interface/reports.html', {'reports': reports})


def report(request, report_id):
    try:
        report = Report.objects.get(pk=report_id)
    except ObjectDoesNotExist:
        report = None
    return render(request, 'mii_interface/report.html', {'report': report})