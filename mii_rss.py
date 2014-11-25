import daemon
import feedparser
import logging
import os
import time
import re
import urllib

import settings

LOG = logging.getLogger(__name__)


def download_torrents():
    LOG.info('Initializing feed')
    feed = feedparser.parse(settings.RSS_URL)

    if feed['status'] != 200:
        LOG.error('Server response not 200: %s' % feed['status'])
        return

    LOG.info('Going through the entries')
    for entry in feed['entries']:
        entry['title'] = entry['title'].lower()
        LOG.info('Entry : %s' % entry['title'])
        for re_filter in settings.RSS_FILTERS:
            LOG.info('Filter : %s' % re_filter)
            if re.match(re_filter, entry['title']):
                LOG.info('Filter is matching')
                file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
                LOG.info('Torrent filename : %s' % file_name)
                if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)):
                    break
                urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))


def main_loop():
    while True:
        LOG.info('Running Feed update')
        download_torrents()
        LOG.info('Sleeping 15min')
        time.sleep(600)

if __name__ == "__main__":
    # with daemon.DaemonContext():
    main_loop()