import json
import feedparser
import os
import re
import urllib


from django.conf import settings
from django.utils import timezone
from pyreport.reporter import Report
from mii_sorter.models import get_serie_episode, get_serie_season, insert_report
from mii_rss.models import FeedDownloaded, FeedEntries
from mii_sorter.sorter import is_serie
from mii_celery import app

logger = Report()


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


def get_or_create_downloading_object(db_name, title):
    regex_result = is_serie(title)
    if regex_result:
        try:
            FeedDownloaded.objects.get(re_filter=db_name, episode=regex_result.group(2), season=regex_result.group(1))
            return False
        except FeedDownloaded.DoesNotExists:
            FeedDownloaded.objects.create(re_filter=db_name, episode=regex_result.group(2),
                                          season=regex_result.group(1), date=timezone.now())
    return True


@app.task()
def check_feed_and_download_torrents():
    logger.create_report()
    logger.info('Initializing feed')
    feed = feedparser.parse(settings.RSS_URL)
    logger.error('Server Exception')
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
            if os.path.exists(os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name)):
                break
            if 'webrip' in file_name.lower():
                break
            if already_exists(settings.RSS_FILTERS[re_filter], entry['title']):
                break
            created = get_or_create_downloading_object(re_filter, entry['title'])
            #Only download when not already downloading the same episode.
            if not created:
                break
            urllib.urlretrieve(entry['link'], os.path.join(settings.TORRENT_WATCHED_FOLDER, file_name))
    insert_report(logger.finalize_report(), report_type='rss')


def get_dict_from_feeds(entry_feeds):
    entries_dict = {'entries': []}
    for entry in entry_feeds:
        entries_dict['entries'].append({'title': entry['title'], 'link': entry['link']})
    return entries_dict


def match(entry, filters):
    for re_filter in filters:
        if re.search(re_filter, entry['title']):
            logger.info('Filter is matching: %s <-> %s' % (re_filter, entry['title']))
            return True, re_filter

    return False, None
