from django.db.models import Model, ForeignKey, FloatField, CharField, OneToOneField

from mii_sorter.models import Movie


QUESTION_CHOICES = [
    ('actor', 'actor'),
    ('story', 'store'),
    ('overall', 'overall'),
    ('director', 'director'),
]


class MovieQuestionSet(Model):
    movie = OneToOneField(Movie, on_delete='CASCADE')


class QuestionAnswer(Model):
    question_set = ForeignKey(MovieQuestionSet, on_delete='CASCADE')
    answer = FloatField()
    question_type = CharField(max_length=50, choices=QUESTION_CHOICES)

    class Meta:
        unique_together = [
            # create a unique on from/to/date
            ['question_set', 'question_type']
        ]