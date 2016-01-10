import json
import logging
import os
import re
import urllib
import feedparser
from django.conf import settings
from pyreport.reporter import Report
from mii_celery import app
from mii_rss.logic import already_exists, get_or_create_downloading_object, get_dict_from_feeds, match
from mii_rss.models import FeedEntries
from mii_sorter.models import insert_report

logger = logging.getLogger(__name__)

if settings.REPORT_ENABLED:
    logger = Report()


@app.task(serializer='json')
def check_feed_and_download_torrents():
    if settings.REPORT_ENABLED:
        logger.create_report()
    logger.info('Initializing feed')
    feed = feedparser.parse(settings.RSS_URL)
    if feed['status'] != 200:
        logger.error('Server response not 200: %s' % feed['status'])
        return

    FeedEntries.objects.create(json_entries=json.dumps(get_dict_from_feeds(feed['entries'])))

    logger.info('Going through the entries')
    for entry in feed['entries']:
        entry['title'] = entry['title'].lower()
        logger.info('Entry : %s' % entry['title'])
        matched, re_filter = match(entry, settings.RSS_FILTERS.keys())
        if matched:
            file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
            logger.info('Torrent filename : %s' % file_name)
            if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)) or \
                    already_exists(settings.RSS_FILTERS[re_filter], entry['title']):
                logger.info('Skipped, already exists')
                continue
            created = get_or_create_downloading_object(re_filter, entry['title'])
            # Only download when not already downloading the same episode.
            if not created:
                logger.info('Skipped, same episode already downloading.')
                continue
            logger.info('Added torrent')
            urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))
    if settings.REPORT_ENABLED:
        insert_report(logger.finalize_report(), report_type='rss')
