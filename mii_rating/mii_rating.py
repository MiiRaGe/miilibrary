from constant.questions import questions
from .models import MovieQuestionSet, QuestionAnswer
from mii_sorter.models import Movie


def get_questions():
    return questions


def save_question_answers(movie_id, question_answers={}):
    movie = Movie.get(id=movie_id)
    movie.seen = True
    movie.save()

    question_set = MovieQuestionSet.get_or_create(movie=movie)

    #Deleting the old questions if any
    QuestionAnswer.delete().where(QuestionAnswer.question_set == question_set).execute()
    question_answers = dict(question_answers)
    del question_answers['action']
    del question_answers['movie_id']
    for question_type, answer in question_answers.items():
        QuestionAnswer.create(question_set=question_set, question_type=question_type, answer=answer[0])


def set_movie_unseen(movie_id):
    movie = Movie.get(id=movie_id)
    movie.seen = False
    movie.save()