import datetime
import logging

from pymongo import MongoClient

import tools



db = MongoClient().miilibrary  # Miilibrary database on the mongo instance

tmdb = db.tmdb  # The Movie Database Collection
osdb = db.osdb  # The Movie Database Collection



def get_or_sync_movie_name(name, year):
    logger = logging.getLogger('NAS')

    logger.info('Querying mongo with name:%s, year:%s' % (name, year))
    existing_data = tmdb.find_one({'name': name, 'year': year}, {'data': 1})

    if existing_data:
        logger.info('Result found in mongo %s' % (existing_data['data']))
        return existing_data['data']

    logger.info('Not found in mongo, querying api with name:%s, year:%s' % (name, year))
    result = tools.MovieDBWrapper.get_movie_name(name, year)

    tmdb.insert({'name': name, 'year': year, 'data': result, 'date': datetime.datetime.now()})
    logger.info('Query saved in mongo')
    return result