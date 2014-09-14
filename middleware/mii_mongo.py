import datetime
import logging

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

import tools

db = None
the_movie_db = None
open_subtitle_db = None
try:
    db = MongoClient().miilibrary  # Miilibrary database on the mongo instance
    the_movie_db = db.tmdb  # The Movie Database Collection
    open_subtitle_db = db.osdb  # OpenSubtitle Collection
except ConnectionFailure, e:
    pass

logger = logging.getLogger('NAS')


# Global tools
def do_query(qry, collection):
    """

    :param qry: dict
    :param collection: pymongo.collection
    :return:
    """
    if not db:
        logger.info('Mongo looks down')
        return
    logger.info('Querying mongo: %s' % qry)
    existing_data = collection.find_one(qry, {'data': 1, 'date': 1})
    if existing_data:
        logger.info('Result found in mongo %s' % (existing_data['data']))
        if (datetime.datetime.now() - existing_data['date']).days > 31:
            logger.info('Too old, querying new data')
        else:
            return existing_data['data']


def do_insert(data, collection):
    if not db:
        return
    collection.insert(data)
    logger.info('Query saved in mongo')


class MiiMongoStored(object):
    qry = {}
    mapping = {}
    collection = None

    def get_or_sync(self, method_name, *args):
        """
        Try to get data from mongo, or call the api and store the result.
        :param method_name: string
        :param args: tuple
        :return: dict
        """
        logger.info('get_or_sync, %s(%s)' % (method_name, args))

        result = do_query(self.qry, self.collection)
        if result:
            return result

        logger.info('Querying the API')
        assert isinstance(method_name, str)
        result = self.mapping[method_name](*args)

        qry = self.qry
        qry.update(data=result, date=datetime.datetime.now())
        do_insert(qry, self.collection)
        return result


class MiiTheMovieDB(MiiMongoStored):
    mapping = {
        'get_movie_imdb_id': tools.MovieDBWrapper.get_movie_imdb_id,
        'get_movie_name': tools.MovieDBWrapper.get_movie_name,
    }
    collection = the_movie_db

    def get_movie_name(self, name, year):
        """
        Return the result of movie query by name/year to The Movie DB
        :param name: string
        :param year: integer
        :return: dict
        """
        self.qry = {'name': name, 'year': year}
        return self.get_or_sync('get_movie_name', name, year)

    def get_movie_imdb_id(self, tmdb_id):
        """
        Return the result of movie query by name/year to The Movie DB
        :param tmdb_id: string
        :return: dict
        """
        self.qry = {'id': tmdb_id}
        return self.get_or_sync('get_movie_imdb_id', tmdb_id)


class MiiOpenSubtitleDB(MiiMongoStored):
    mapping = {
        'get_imdb_information': tools.OpensubtitleWrapper.get_imdb_information,
        'get_movie_names': tools.OpensubtitleWrapper.get_movie_names,
        'get_movie_names2': tools.OpensubtitleWrapper.get_movie_names2,
        'get_subtitles': tools.OpensubtitleWrapper.get_subtitles,
    }
    collection = open_subtitle_db

    def get_imdb_information(self, imdb_id):
        """
        Get all the imdb information from opensubtitle api
        :param imdb_id: string
        :return: dict
        """
        self.qry = {'id': imdb_id}
        return self.get_or_sync('get_imdb_information', imdb_id)

    def get_movie_name(self, movie_hash, number=''):
        """
        Return the movie name (and other information) from a hash
        :param movie_hash: string
        :param number: integer
        :return: dict
        """
        self.qry = {'movie_hash': movie_hash}
        return self.get_or_sync('get_movie_names%s' % number, [movie_hash])

    def get_subtitles(self, movie_hash, file_size):
        """
        Get the list of subtitles associated to a file hash
        :param movie_hash: string
        :param file_size: int
        :return: dict
        """
        self.qry = {'movie_hash': movie_hash, 'file_size': file_size}
        return self.get_or_sync('get_subtitles', movie_hash, file_size, '')

