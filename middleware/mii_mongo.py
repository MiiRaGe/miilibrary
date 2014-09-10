import datetime
import logging

from pymongo import MongoClient

import tools


db = MongoClient().miilibrary  # Miilibrary database on the mongo instance

tmdb = db.tmdb  # The Movie Database Collection
osdb = db.osdb  # Opensubtitle Collection

# Global tools


class MiiMongo():
    def __init__(self):
        self.logger = logging.getLogger('NAS')

    def do_query(self, qry, collection):
        self.logger.info('Querying mongo: %s' % qry)
        existing_data = collection.find_one(qry, {'data': 1, 'date': 1})
        if existing_data:
            self.logger.info('Result found in mongo %s' % (existing_data['data']))
            if (datetime.datetime.now() - existing_data['date']).days > 31:
                self.logger.info('Too old, querying new data')
            else:
                return existing_data['data']

    def do_insert(self, data, collection):
        collection.insert(data)
        self.logger.info('Query saved in mongo')

    # Open Subtitle Database

    def get_or_sync_imdb_information(self, id):
        self.logger.info('get_or_sync_imdb_information(%s)' % id)

        result = self.do_query({'id': id}, osdb)
        if result:
            return result

        self.logger.info('Querying the API')
        result = tools.OpensubtitleWrapper.get_imdb_information(id)

        self.do_insert({'id': id, 'data': result, 'date': datetime.datetime.now()}, osdb)
        return result

    # The Movie DB

    def get_or_sync_movie_name(self, name, year):
        self.logger.info('get_or_sync_movie_name(%s, %s)' % (name, year))

        result = self.do_query({'name': name, 'year': year}, tmdb)
        if result:
            return result

        self.logger.info('Querying the API')
        result = tools.MovieDBWrapper.get_movie_name(name, year)

        self.do_insert({'name': name, 'year': year, 'data': result, 'date': datetime.datetime.now()}, tmdb)
        return result

    def get_or_sync_movie_imdb_id(self, id):
        self.logger.info('get_or_sync_movie_imdb_id(%s)' % id)

        result = self.do_query({'id': id}, tmdb)
        if result:
            return result

        self.logger.info('Querying the API')
        result = tools.MovieDBWrapper.get_movie_imdb_id(id)

        self.do_insert({'id': id, 'data': result, 'date': datetime.datetime.now()}, tmdb)
        return result
