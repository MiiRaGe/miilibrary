from peewee import *

import settings

db = SqliteDatabase("%s" % settings.DB_NAME)


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


def insert_serie_episode(serie_name, serie_season, episode_number, serie_path):
    serie = Serie(name=serie_name, season=serie_season, episode=episode_number, file_path=serie_path)
    serie.save()


def insert_movie(title, year, path):
    movie = Movie(title=title, year=year, folder_path=path)
    movie.save()
    return movie
