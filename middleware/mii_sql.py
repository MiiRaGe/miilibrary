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
    name = CharField(unique=True)


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


class MovieTagging(MiiBase):
    movie = ForeignKeyField(Movie)
    tag = ForeignKeyField(Tag)


class Person(MiiBase):
    name = CharField(unique=True)


class MovieRelation(MiiBase):
    uid = CharField(unique=True)
    movie = ForeignKeyField(Movie)
    person = ForeignKeyField(Person)
    type = CharField()


class WhatsNew(MiiBase):
    date = DateTimeField()
    name = CharField(unique=True)
    path = CharField()

    class Meta:
        order_by = ('date', )


class Unpacked(MiiBase):
    filename = TextField()


class FeedDownloaded(MiiBase):
    date = DateTimeField(default=datetime.datetime(1900, 1, 1))
    re_filter = CharField(unique=True)


TABLE_LIST = [Movie, MovieTagging, Tag, MovieTagging, Serie, Episode, Season, WhatsNew, Unpacked,
              FeedDownloaded, MovieRelation, Person]
db.create_tables(TABLE_LIST,
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


def get_serie_season(name, season):
    """
    Look for the same season in the db, returns a boolean
    :param string name: string
    :param int season: integer
    :return bool:
    """
    try:
        logger.info('Querying serie table with name=%s and season=%s' % (name, season))
        season = Season.select().join(Season).join(Serie).where(Season.number == season,
                                                                Serie.name == name).get()
        if season:
            return True
    except (Serie.DoesNotExist, Season.DoesNotExist) as e:
        logger.info('Found nothing %s' % repr(e))
        return False


def insert_serie_episode(serie_name, serie_season, episode_number, serie_path, size):
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

    episode = Episode.get_or_create(number=episode_number, season=season, file_path=serie_path, file_size=size)
    episode.save()

    # Add the serie to the what's new folder
    wn = WhatsNew.get_or_create(name='%s S%sE%s' % (serie_name, serie_season, episode_number),
                                date=datetime.datetime.now(),
                                path=serie_path)
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


def insert_movie(title, year, path, size):
    """
    Insert a movie into the sql database following Movie model.
    :param string title: Title of the movie
    :param int year: Year of the movie
    :param string path: Path of the movie file
    :return Movie: Movie instance to be modified with additional data
    :rtype Movie: Movie type
    """
    movie = Movie.get_or_create(title=title, year=year, folder_path=path, file_size=size)
    movie.save()

    # Add the movie to the what's new folder
    wn = WhatsNew.get_or_create(name='%s (%s)' % (title, year), date=datetime.datetime.now(), path=path)
    wn.save()

    return movie
