import daemon
import feedparser
import logging
import os
import time
import re
import urllib

import settings

logging.basicConfig(filename='example.log', level=logging.DEBUG)

downloaded_files = {}


def download_torrents():
    logging.info('Initializing feed')
    feed = feedparser.parse(settings.RSS_URL)

    if feed['status'] != 200:
        logging.error('Server response not 200: %s' % feed['status'])
        return

    logging.info('Going through the entries')
    for entry in feed['entries']:
        entry['title'] = entry['title'].lower()
        logging.info('Entry : %s' % entry['title'])
        matched, re_filter = match(entry, settings.RSS_FILTERS)
        if matched:
            file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
            logging.info('Torrent filename : %s' % file_name)
            if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)):
                break
            if 'webrip' in file_name.lower():
                break

            if not downloaded_files.get(re_filter):
                downloaded_files[re_filter] = True
                urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))
            else:
                logging.info('Skipping %s as already downloaded' % file_name)


def match(entry, filters):
    for re_filter in filters:
        logging.info('Filter : %s' % re_filter)
        if re.search(re_filter, entry['title']):
            logging.info('Filter is matching')
            return True, re_filter
    return False, None


def main_loop():
    while True:
        logging.info('Running Feed update')
        download_torrents()
        logging.info('Sleeping 15min')
        time.sleep(600)

if __name__ == "__main__":
    with daemon.DaemonContext():
        main_loop()
