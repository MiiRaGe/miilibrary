from mii_rating.constant.questions import questions
from mii_rating.models import MovieQuestionSet, QuestionAnswer
from mii_sorter.models import Movie


def get_questions():
    return questions


def save_question_answers(movie_id, question_answers={}):
    movie = Movie.objects.get(id=movie_id)
    movie.seen = True
    movie.save()

    question_set, created = MovieQuestionSet.objects.get_or_create(movie=movie)

    #Deleting the old questions if any
    QuestionAnswer.objects.filter(question_set_id=question_set.id).delete()
    question_answers = dict(question_answers)
    del question_answers['action']
    del question_answers['movie_id']
    for question_type, answer in question_answers.items():
        QuestionAnswer.objects.create(question_set_id=question_set.id, question_type=question_type, answer=answer[0])


def set_movie_unseen(movie_id):
    movie = Movie.objects.get(id=movie_id)
    movie.seen = False
    movie.save()
