import base64
import json
import logging
import os
import re
import tempfile
import urllib
import feedparser
from datetime import timedelta

import requests
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from pyreport.reporter import Report
from mii_celery import app
from mii_rss.logic import already_exists, get_or_create_downloading_object, get_dict_from_feeds, match
from mii_rss.models import FeedEntries, FeedFilter
from mii_sorter.models import insert_report

logger = logging.getLogger(__name__)

if settings.REPORT_ENABLED:
    logger = Report()


@app.task(serializer='json')
def recheck_feed_and_download_torrents():
    if settings.REPORT_ENABLED:
        logger.create_report()
    json_feeds = FeedEntries.objects.filter(date__gte=timezone.now() - timedelta(days=2)) \
        .values_list('json_entries', flat=True)
    feeds = [json.loads(x) for x in json_feeds]
    for feed_entries in feeds:
        process_feeds(feed_entries['entries'])
    if settings.REPORT_ENABLED:
        insert_report(logger.finalize_report(), report_type='recheck_rss')


@app.task(serializer='json')
def check_feed_and_download_torrents():
    if settings.REPORT_ENABLED:
        logger.create_report()
    logger.info(u'Initializing feed')
    feed = feedparser.parse(settings.RSS_URL)
    if feed['status'] != 200:
        logger.error(u'Server response not 200: %s' % feed['status'])
        return

    FeedEntries.objects.create(json_entries=json.dumps(get_dict_from_feeds(feed['entries'])))

    logger.info(u'Going through the entries')
    process_feeds(feed['entries'])
    if settings.REPORT_ENABLED:
        insert_report(logger.finalize_report(), report_type='rss')


def process_feeds(entries):
    filters = dict(FeedFilter.objects.all().values_list('regex', 'name'))
    for entry in entries:
        entry['title'] = entry['title'].lower()
        logger.info(u'Entry : %s' % entry['title'])
        matched, re_filter = match(entry, filters.keys())
        if matched:
            file_name = re.search('/([^\/]*\.torrent)\?', entry['link']).group(1)
            logger.info(u'Torrent filename : %s' % file_name)
            if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)) or \
                    already_exists(filters[re_filter], entry['title']):
                logger.info(u'Skipped, already exists')
                continue
            created = get_or_create_downloading_object(re_filter, entry['title'])
            # Only download when not already downloading the same episode.
            if not created:
                logger.info(u'Skipped, same episode already downloading.')
                continue
            logger.info(u'Added torrent')
            add_torrent_to_transmission.delay(entry['link'])


@app.task(serializer='json', bind=True)
def add_torrent_to_transmission(self, url_link):
    if cache.get(url_link) and False:
        print u'Fetching data from the cache'
        content = cache.get(url_link)
    else:
        print u'Getting data from the url'
        resp = requests.get(url_link)
        content = resp.content
        key = 'base64,'
        if key in content:
            index = content.index(key)
            content = content[index + len(key):]
        content = base64.b64encode(content)
        cache.set(url_link, content, 600)
        print u'Seting data in the cache'

    parameters = {
        "method": "torrent-add",
        "arguments": {
            "metainfo": content,
            "download-dir": settings.SOURCE_FOLDER,
            "paused": False
        }
    }
    headers = {
        'Content-Type': 'json'
    }
    if cache.get('X-Transmission-Session-Id'):
        print u'Getting session id from cache'
        headers['X-Transmission-Session-Id'] = cache.get('X-Transmission-Session-Id')
    print u'Posting torrent to transmission'
    response = requests.post(settings.TRANSMISSION_RPC_URL, json=parameters, headers=headers, auth=(settings.TRANSMISSION_RPC_USERNAME, settings.TRANSMISSION_RPC_PASSWORD))
    print u'Got Answer %s' % response.status_code
    if response.status_code == 409:
        cache.set('X-Transmission-Session-Id', response.headers['X-Transmission-Session-Id'], 3600)
        self.retry(countdown=10, max_retries=5)
    elif response.status_code == 500:
        raise Exception('The task actually failed %s', response.content)
    elif response.status_code != 200:
        raise Exception('The task actually failed with status %s', response.status_code)
    result_dict = json.loads(response.content)
    if result_dict['result'] != 'success':
        raise Exception('Adding new Torrent failed: %s' % result_dict)