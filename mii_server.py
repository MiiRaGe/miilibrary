from flask import Flask, render_template

from middleware.mii_sql import Movie, Serie

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

if __name__ == "__main__":
    app.run(host='0.0.0.0')