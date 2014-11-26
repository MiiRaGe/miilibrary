import datetime
import logging

from peewee import *

import settings

db = MySQLDatabase(settings.MYSQL_NAME,
                   host=settings.MYSQL_HOST,
                   port=settings.MYSQL_PORT,
                   user=settings.MYSQL_USERNAME,
                   password=settings.MYSQL_PASSWORD)
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
    file_size = BigIntegerField()

    class Meta:
        indexes = (
            (('title', 'year'), True),
        )
        order_by = ('year', 'title')


class Tag(MiiBase):
    name = CharField()


class Serie(MiiBase):
    name = CharField()

    class Meta:
        order_by = ('name',)


class Season(MiiBase):
    number = IntegerField()
    serie = ForeignKeyField(Serie, related_name='seasons', on_delete='CASCADE')


class Episode(MiiBase):
    number = IntegerField()
    season = ForeignKeyField(Season, related_name='episodes', on_delete='CASCADE')
    file_path = CharField()
    file_size = BigIntegerField()


class SerieTagging(MiiBase):
    serie = ForeignKeyField(Serie)
    tag = ForeignKeyField(Tag)


class MovieTagging(MiiBase):
    movie = ForeignKeyField(Movie)
    tag = ForeignKeyField(Tag)


class WhatsNew(MiiBase):
    date = DateTimeField()
    name = CharField(unique=True)
    path = CharField()

    class Meta:
        order_by = ('date', )


class Unpacked(MiiBase):
    filename = TextField()


db.create_tables([Movie, MovieTagging, Tag, MovieTagging, Serie, SerieTagging, Episode, Season, WhatsNew, Unpacked],
                 safe=True)
try:
    db.execute_sql("create view summary as "
               "select serie.name as 'Name', season.number as 'Season', episode.number as 'Episode'"
               "from serie"
               "     inner join season on season.serie_id = serie.id "
               "        inner join episode on episode.season_id = season.id "
               "order by serie.name, season.number, episode.number;")
except:
    pass


def get_serie_episode(name, season, episode):
    """
    Look for the same episode in the db, return the file_path of the existing one if any.
    :param string name: string
    :param int season: integer
    :param int episode: integer
    :return tuple: Tuple containing the path is serie is found (Boolean, String)
    """
    try:
        logger.info('Querying serie table with name=%s, season=%s and episode=%s' % (name, season, episode))
        episode = Episode.select().join(Season).join(Serie).where(Season.number == season,
                                                                  Episode.number == episode,
                                                                  Serie.name == name).get()
        if episode:
            return True, episode
    except (Serie.DoesNotExist, Season.DoesNotExist, Episode.DoesNotExist) as e:
        logger.info('Found nothing %s' % repr(e))
        return False, None


def insert_serie_episode(serie_name, serie_season, episode_number, serie_path):
    """
    Insert a serie into the sql database following Serie model.
    :param string serie_name: Name of the serie
    :param int serie_season: Season number
    :param int episode_number: Episode number
    :param string serie_path: Path of the file
    :rtype Episode: Episode of the serie
    """

    serie = Serie.get_or_create(name=serie_name)
    serie.save()

    season = Season.get_or_create(number=serie_season, serie=serie)
    season.save()

    episode = Episode(number=episode_number, season=season, file_path=serie_path)
    episode.save()

    # Add the serie to the what's new folder
    wn = WhatsNew.get_or_create(name='%s S%sE%s' % (serie_name, serie_season, episode_number))
    wn.date = datetime.datetime.now()
    wn.path = serie_path
    wn.save()

    return episode


def get_movie(title, year=None):
    """
    Look for the same movie in the db, return the file_path of the existing one if any.
    :param string title: string
    :param int year: integer
    :return tuple: Tuple containing the path is movie is found (Boolean, String)
    :rtype (bool, Movie):
    """
    try:
        logger.info('Querying movie table with name=%s and year=%s' % (title, year))
        if year:
            movie = Movie.get(title=title, year=year)
        else:
            movie = Movie.get(title=title)
        logger.info('Found movie')
        return True, movie
    except Movie.DoesNotExist as e:
        logger.info('Found nothing %s' % repr(e))
        return False, None


def insert_movie(title, year, path):
    """
    Insert a movie into the sql database following Movie model.
    :param string title: Title of the movie
    :param int year: Year of the movie
    :param string path: Path of the movie file
    :return Movie: Movie instance to be modified with additional data
    :rtype Movie: Movie type
    """
    movie = Movie(title=title, year=year, folder_path=path)
    movie.save()

    # Add the movie to the what's new folder
    wn = WhatsNew.get_or_create(name='%s (%s)' % (title, year))
    wn.date = datetime.datetime.now()
    wn.path = path
    wn.save()
    
    return movie
