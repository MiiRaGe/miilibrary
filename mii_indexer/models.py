from django.db.models import Model, CharField, ForeignKey
from mii_sorter.models import Movie

__author__ = 'MiiRaGe'


class Tag(Model):
    name = CharField(unique=True, max_length=50)

    def __str__(self):
        return self.name


class MovieTagging(Model):
    movie = ForeignKey(Movie)
    tag = ForeignKey(Tag)

    class Meta:
        unique_together = [
            'movie', 'tag'
        ]

    def __str__(self):
        return '{} -> {}'.format(self.tag.name, self.movie.title)


class Person(Model):
    name = CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name


class MovieRelation(Model):
    movie = ForeignKey(Movie)
    person = ForeignKey(Person)
    type = CharField(max_length=10)

    class Meta:
        unique_together = [
            'movie', 'person', 'type'
        ]

    def __str__(self):
        return '{} is {} in {}'.format(self.person.name, self.type, self.movie.title)
