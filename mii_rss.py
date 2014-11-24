import daemon
import feedparser
import os
import time
import re
import urllib

import settings


def download_torrents():
    feed = feedparser.parse(settings.RSS_URL)

    if feed['status'] != 200:
        return

    for entry in feed['entries']:
        entry['title'] = entry['title'].lower()
        file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
        for re_filter in settings.RSS_FILTERS:
            if re.match(re_filter, entry['title']):
                if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)):
                    break
                urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))


def main_loop():
    while True:
        download_torrents()
        time.sleep(3600)

if __name__ == "__main__":
    with daemon.DaemonContext():
        main_loop()