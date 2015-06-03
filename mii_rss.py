import datetime
import feedparser
import logging
import os
import time
import re
import urllib

import settings
from middleware.mii_sql import FeedDownloaded, get_serie_episode, get_serie_season, db
from sorter.sorter import is_serie

logging.basicConfig(filename='example.log', level=logging.DEBUG)


def already_exists(db_name, title):
    regex_result = is_serie(title)
    if regex_result:
        if get_serie_episode(db_name, regex_result.group(1), regex_result.group(2))[0]:
            return True
        else:
            return False
    matched = re.match('.*%s.*S(\d\d)', title)
    if matched and get_serie_season(title, matched.group(1)):
        return True
    return False


def already_downloading(db_name, title):
    regex_result = is_serie(title)
    if regex_result:
        try:
            FeedDownloaded.get(re_filter=db_name, episode=regex_result.group(2), season=regex_result.group(1))
            return True
        except FeedDownloaded.DoesNotExists:
            FeedDownloaded.create(re_filter=db_name, episode=regex_result.group(2), season=regex_result.group(1),
                                  date=datetime.datetime.now())
    return False


def download_torrents():
    db.connect()
    logging.info('Initializing feed')
    try:
        feed = feedparser.parse(settings.RSS_URL)
        logging.error('Server Exception')
        if feed['status'] != 200:
            logging.error('Server response not 200: %s' % feed['status'])
            return
    except Exception as e:
        logging.exception('Server exception: %s' % repr(e))
        return

    logging.info('Going through the entries')
    for entry in feed['entries']:
        entry['title'] = entry['title'].lower()
        logging.info('Entry : %s' % entry['title'])
        matched, re_filter = match(entry, settings.RSS_FILTERS.keys())
        if matched:
            file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
            logging.info('Torrent filename : %s' % file_name)
            if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)):
                break
            if 'webrip' in file_name.lower():
                break
            if already_exists(settings.RSS_FILTERS[re_filter], entry['title']):
                break
            if already_downloading(re_filter, entry['title']):
                break
            urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))


def match(entry, filters):
    for re_filter in filters:
        logging.info('Filter : %s' % re_filter)
        if re.search(re_filter, entry['title']):
            logging.info('Filter is matching')
            return True, re_filter
        else:
            print '%s != %s' % (re_filter, entry['title'])

    return False, None


def main_loop():
    while True:
        logging.info('Running Feed update')
        download_torrents()
        logging.info('Sleeping 15min')
        time.sleep(3600)


if __name__ == "__main__":
    main_loop()
