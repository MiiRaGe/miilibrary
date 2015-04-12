from flask import Flask, render_template, request
from peewee import fn

from middleware.mii_sql import Movie, Serie
from rating.mii_rating import get_questions, save_question_answers, set_movie_unseen

app = Flask(__name__)


@app.route("/")
def index():
    try:
        return render_template('/index.html')
    except Exception as e:
        return repr(e)


@app.route("/movies")
def movies():
    try:
        return render_template('/movie.html', movies=[x for x in Movie.select()])
    except Exception as e:
        return repr(e)

@app.route("/series")
def series():
    try:
        return render_template('/serie.html', series=[x for x in Serie.select()])
    except Exception as e:
        return repr(e)

@app.route("/rate", methods=['GET', 'POST'])
def rate():
    try:
        questions = get_questions()
        movie = Movie.select().where(Movie.seen == None).order_by(fn.Rand()).limit(1)[0]

        if request.method == 'POST':
            data = request.form
            action = data.get('action')
            if action == 'save_movie':
                save_question_answers(data['movie_id'], question_answers=data)
            elif action == 'not_seen':
                set_movie_unseen(data['movie_id'])

        return render_template('/rate.html', questions=questions, movie=movie)
    except Exception as e:
        return repr(e)


if __name__ == "__main__":
    app.run(host='0.0.0.0')