import logging
import os

from peewee import *

import settings

db = SqliteDatabase("%s" % os.path.join(settings.DESTINATION_FOLDER, settings.DB_NAME))

logger = logging.getLogger('NAS')


class MiiBase(Model):
    class Meta:
        database = db


class Movie(MiiBase):
    title = CharField()
    year = IntegerField(null=True, default=1900)
    imdb_id = CharField(null=True)
    rating = FloatField(null=True)
    folder_path = CharField()

    class Meta:
        database = db
        indexes = (
            (('title', 'year'), True),
        )
        order_by = ('year', 'title')


class Tag(MiiBase):
    name = CharField()

    class Meta:
        database = db


class Serie(MiiBase):
    name = CharField()
    season = IntegerField()
    episode = IntegerField()
    file_path = CharField()

    class Meta:
        database = db
        indexes = (
            (('name', 'season', 'episode'), True),
        )
        order_by = ('name', 'season', 'episode')


class SerieTagging(MiiBase):
    serie = ForeignKeyField(Serie)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = db


class MovieTagging(MiiBase):
    movie = ForeignKeyField(Movie)
    tag = ForeignKeyField(Tag)

    class Meta:
        database = db


db.create_tables([Movie, MovieTagging, Tag, MovieTagging, Serie, SerieTagging], safe=True)


def get_serie_episode(serie_name, serie_season, episode_number):
    """
    Look for the same episode in the db, return the file_path of the existing one if any.
    :param serie_name: string
    :param serie_season: integer
    :param episode_number: integer
    :return: tuple
    """
    serie = Serie.get(name=serie_name, season=serie_season, episode=episode_number)
    if serie:
        return True, serie.file_path
    return False,


def insert_serie_episode(serie_name, serie_season, episode_number, serie_path):
    """
    Insert a serie into the sql database following Serie model.
    :param serie_name: string
    :param serie_season: integer
    :param episode_number: integer
    :param serie_path: string
    """
    serie = Serie(name=serie_name, season=serie_season, episode=episode_number, file_path=serie_path)
    serie.save()


def insert_movie(title, year, path):
    """
    Insert a movie into the sql database following Movie model.
    :param title: string
    :param year: integer
    :param path: string
    :return: Movie
    """
    movie = Movie(title=title, year=year, folder_path=path)
    movie.save()
    return movie
