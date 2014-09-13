import datetime
import logging

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

import tools

db = None
tmdb = None
osdb = None
try:
    db = MongoClient().miilibrary  # Miilibrary database on the mongo instance
    tmdb = db.tmdb  # The Movie Database Collection
    osdb = db.osdb  # Opensubtitle Collection
except ConnectionFailure, e:
    pass

# Global tools


class MiiMongoStored(object):
    qry = {}
    mapping = {}
    logger = logging.getLogger('NAS')
    collection = None

    def do_query(self, qry, collection):
        if not db:
            self.logger.info('Mongo looks down')
            return
        self.logger.info('Querying mongo: %s' % qry)
        existing_data = collection.find_one(qry, {'data': 1, 'date': 1})
        if existing_data:
            self.logger.info('Result found in mongo %s' % (existing_data['data']))
            if (datetime.datetime.now() - existing_data['date']).days > 31:
                self.logger.info('Too old, querying new data')
            else:
                return existing_data['data']

    def do_insert(self, data, collection):
        if not db:
            return
        collection.insert(data)
        self.logger.info('Query saved in mongo')

    def get_or_sync(self, method_name, *args, **kwargs):
        self.logger.info('get_or_sync, %s(%s)' % (method_name, args))

        result = self.do_query(self.qry, self.collection)
        if result:
            return result

        self.logger.info('Querying the API')
        result = self.mapping[method_name](*args)

        qry = self.qry
        qry.update(data=result, date=datetime.datetime.now())
        self.do_insert(qry, self.collection)
        return result


class MiiTMDB(MiiMongoStored):
    mapping = {
        'get_movie_imdb_id': tools.MovieDBWrapper.get_movie_imdb_id,
        'get_movie_name': tools.MovieDBWrapper.get_movie_name,
    }
    collection = tmdb

    def get_movie_name(self, name, year):
        self.qry = {'name': name, 'year': year}
        return self.get_or_sync('get_movie_name', name, year)

    def get_movie_imdb_id(self, id):
        self.qry = {'id': id}
        return self.get_or_sync('get_movie_imdb_id', id)


class MiiOSDB(MiiMongoStored):
    mapping = {
        'get_imdb_information': tools.OpensubtitleWrapper.get_imdb_information,
        'get_movie_names': tools.OpensubtitleWrapper.get_movie_names,
        'get_movie_names2': tools.OpensubtitleWrapper.get_movie_names2,
        'get_subtitles': tools.OpensubtitleWrapper.get_subtitles,
    }
    collection = osdb

    def get_imdb_information(self, id):
        self.qry = {'id': id}
        return self.get_or_sync('get_imdb_information', id)

    def get_movie_name(self, movie_hash, number=''):
        self.qry = {'movie_hash': movie_hash}
        return self.get_or_sync('get_movie_names%s' % number, [movie_hash])

    def get_subtitles(self, movie_hash, file_size):
        self.qry = {'movie_hash': movie_hash, 'file_size': file_size}
        return self.get_or_sync('get_subtitles', movie_hash, file_size, '')

