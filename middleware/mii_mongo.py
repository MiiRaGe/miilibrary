import logging

from django.conf import settings
from django.utils import timezone
from pymongo import MongoClient
from middleware.models import JSONKeyValue
from movieinfo.opensubtitle_wrapper import OpenSubtitleWrapper
from movieinfo.the_movie_db_wrapper import TheMovieDBWrapper


logger = logging.getLogger('NAS')

db = None
the_movie_db = None
open_subtitle_db = None
client = MongoClient(host='mongodb://%s:%s@%s:%s/%s' % (settings.MONGO_USERNAME,
                                                        settings.MONGO_PASSWORD,
                                                        settings.MONGO_HOST,
                                                        settings.MONGO_PORT,
                                                        settings.MONGO_DB_NAME))
db = client[settings.MONGO_DB_NAME]


# Global tools
def do_query(qry, collection):
    """

    :param qry: dict
    :param collection: type
    :return: dict
    """
    if not db:
        logger.info('Mongo looks down')
        return
    logger.info('Querying mongo: %s' % qry)
    existing_data = collection.find_one(qry, {'data': 1, 'date': 1})
    if existing_data:
        logger.info('Result found in mongo')
        return existing_data['data']


def do_insert(data, collection):
    """
    Insert the API result in mongo
    :param data: dict
    :param collection: type
    """
    if db:
        collection.insert(data)
        logger.info('Query saved in mongo')


class MiiMongoStored(object):
    key = {}
    mapping = {}
    type = None

    def get_or_sync(self, method_name, *args):
        """
        Try to get data from mongo, or call the api and store the result.
        :param string method_name: Name of the API method to sync the data
        :param tuple args: *args for the API method
        :return dict: JSON returned by the API or from the db
        """
        logger.info('get_or_sync, %s(%s)' % (method_name, args))

        result = JSONKeyValue.get(self.type, self.key)
        if result != 0:
            return result

        logger.info('Querying the API')
        result = self.mapping[method_name](*args)
        JSONKeyValue.set(self.type, self.key, result)

        return result


class MiiTheMovieDB(MiiMongoStored):
    the_movie_db_wrapper = TheMovieDBWrapper()
    mapping = {
        'get_movie_imdb_id': the_movie_db_wrapper.get_movie_imdb_id,
        'get_movie_name': the_movie_db_wrapper.get_movie_name,
    }
    type = db.tmdb if db else None

    def get_movie_name(self, name, year):
        """
        Return the result of movie query by name/year to The Movie DB
        :param string name: name of the movie
        :param integer year: year of the movie
        :return dict: JSON returned by the API with information about the movie
        """
        self.key = {'name': name, 'year': year}
        return self.get_or_sync('get_movie_name', name, year)

    def get_movie_imdb_id(self, tmdb_id):
        """
        Return the result of movie query by name/year to The Movie DB
        :param string tmdb_id: The Movie Database ID (gotten from name/year query)
        :return dict: JSON returned by the API with the IMDB ID of the movie
        """
        self.key = {'id': tmdb_id}
        return self.get_or_sync('get_movie_imdb_id', tmdb_id)


class MiiOpenSubtitleDB(MiiMongoStored):
    open_subtitle_wrapper = OpenSubtitleWrapper()
    mapping = {
        'get_imdb_information': open_subtitle_wrapper.get_imdb_information,
        'get_movie_names': open_subtitle_wrapper.get_movie_names,
        'get_movie_names2': open_subtitle_wrapper.get_movie_names2,
        'get_subtitles': open_subtitle_wrapper.get_subtitles,
    }
    type = db.osdb if db else None

    def get_imdb_information(self, imdb_id):
        """
        Get all the imdb information from opensubtitle api
        :param string imdb_id: IMDB ID to get the information on
        :return dict: All the information about a movie from IMDB
        """
        self.key = {'id': imdb_id}
        return self.get_or_sync('get_imdb_information', imdb_id)

    def get_movie_name(self, movie_hash, number=''):
        """
        Return the movie name (and other information) from a hash
        :param string movie_hash: String representing the special hash used by open subtitle
        :param integer number: Type of API method to call (can be either '' or '2' differences are unknown)
        :return dict: Return the movie information as JSON
        """
        self.key = {'movie_hash': movie_hash}
        return self.get_or_sync('get_movie_names%s' % number, [movie_hash])

    def get_subtitles(self, movie_hash, file_size):
        """
        Get the list of subtitles associated to a file hash
        :param string movie_hash: String representing the special hash used by open subtitle
        :param int file_size: Size of the movie
        :return dict: Return the JSON containing information about different available subtitles
        """
        self.key = {'movie_hash': movie_hash, 'file_size': file_size}
        return self.get_or_sync('get_subtitles', movie_hash, file_size, '')

