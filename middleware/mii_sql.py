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
    :param string serie_name: string
    :param int serie_season: integer
    :param int episode_number: integer
    :return tuple: Tuple containing the path is serie is found (Boolean, String)
    """
    try:
        serie = Serie.get(name=serie_name, season=serie_season, episode=episode_number)
        if serie:
            return True, serie.file_path
    except Exception as e:
        return False,



def insert_serie_episode(serie_name, serie_season, episode_number, serie_path):
    """
    Insert a serie into the sql database following Serie model.
    :param string serie_name: Name of the serie
    :param int serie_season: Season number
    :param int episode_number: Episode number
    :param string serie_path: Path of the file
    """
    serie = Serie(name=serie_name, season=serie_season, episode=episode_number, file_path=serie_path)
    serie.save()


def insert_movie(title, year, path):
    """
    Insert a movie into the sql database following Movie model.
    :param string title: Title of the movie
    :param int year: Year of the movie
    :param string path: Path of the movie file
    :return Movie: Movie instance to be modified with additional data
    """
    movie = Movie(title=title, year=year, folder_path=path)
    movie.save()
    return movie
