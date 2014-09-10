import datetime
import logging

from pymongo import MongoClient

import tools



db = MongoClient().miilibrary  # Miilibrary database on the mongo instance

tmdb = db.tmdb  # The Movie Database Collection
osdb = db.osdb  # Opensubtitle Collection


def get_or_sync_movie_name(name, year):
    logger = logging.getLogger('NAS')
    logger.info('get_or_sync_movie_name(%s, %s)' % (name, year))

    logger.info('Querying mongo')
    existing_data = tmdb.find_one({'name': name, 'year': year}, {'data': 1, 'date': 1})

    if existing_data:
        logger.info('Result found in mongo %s' % (existing_data['data']))
        if (datetime.datetime.now() - existing_data['date']).days > 31:
            logger.info('Too old, querying new data')
        else:
            return existing_data['data']

    logger.info('Querying api')
    result = tools.MovieDBWrapper.get_movie_name(name, year)

    tmdb.insert({'name': name, 'year': year, 'data': result, 'date': datetime.datetime.now()})
    logger.info('Query saved in mongo')
    return result


def get_or_sync_movie_imdb_id(id):
    logger = logging.getLogger('NAS')
    logger.info('get_or_sync_movie_imdb_id(%s)' % id)
    logger.info('Querying mongo')
    existing_data = tmdb.find_one({'id': id}, {'data': 1, 'date': 1})

    if existing_data:
        logger.info('Result found in mongo %s' % (existing_data['data']))
        if (datetime.datetime.now() - existing_data['date']).days > 31:
            logger.info('Too old, querying new data')
        else:
            return existing_data['data']

    logger.info('Querying api' % id)
    result = tools.MovieDBWrapper.get_movie_imdb_id(id)

    tmdb.insert({'id': id, 'data': result, 'date': datetime.datetime.now()})
    logger.info('Query saved in mongo')
    return result