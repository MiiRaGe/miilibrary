import json
from django.shortcuts import render

from mii_indexer.models import Tag, MovieTagging, MovieRelation
from mii_sorter.models import Movie, Serie
from mii_rating.mii_rating import get_questions, save_question_answers, set_movie_unseen


def index(request):
    return render(request, 'mii_interface/index.html')


def movies(request):
    try:
        return render(request, 'mii_interface/movie.html', dict(movies=[x for x in Movie.select()]))
    except Exception as e:
        return repr(e)


def series(request):
    try:
        return render(request, 'mii_interface/serie.html', dict(series=[x for x in Serie.select()]))
    except Exception as e:
        return repr(e)


def rate(request):
    questions = get_questions()
    movie = Movie.select().where(Movie.seen == None).order_by(fn.Rand()).limit(1)[0]
    movie = []

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
            movie = Movie.get(id=movie_id)
        except DoesNotExist:
            pass

    movies_choices_json = json.dumps([{'label': x.title, 'value': x.id} for x in Movie.select()])
    genres = [x.tag.name for x in MovieTagging.filter(movie=movie)]
    actors = [x.person.name for x in MovieRelation.filter(movie=movie, type='Actor')]
    directors = [x.person.name for x in MovieRelation.filter(movie=movie, type='Director')]
    return render(request, 'mii_interface/rate.html', dict(questions=questions, movie=movie, movies_choices_json=movies_choices_json,
                           genres=genres, actors=actors, directors=directors))