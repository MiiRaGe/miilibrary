import re

from django.core.exceptions import ObjectDoesNotExist

from mii_rss.models import FeedDownloaded
from mii_sorter.models import get_serie_episode, get_serie_season
from mii_sorter.sorter import is_serie


def already_exists(db_name, title):
    regex_result = is_serie(title)
    if regex_result:
        if get_serie_episode(db_name, regex_result.group(1), regex_result.group(2))[0]:
            return True
        else:
            return False
    matched = re.match('.*%s.*S(\d\d)' % db_name, title)
    if matched and get_serie_season(db_name, matched.group(1)):
        return True
    return False


def get_or_create_downloading_object(db_name, title):
    regex_result = is_serie(title)
    if regex_result:
        try:
            # Tests that the episode isn't already being downloaded
            FeedDownloaded.objects.get(re_filter=db_name, episode=regex_result.group(2), season=regex_result.group(1))
            return False
        except ObjectDoesNotExist:
            # Make sure the season is not already being downloaded or downloaded entirely already.
            if FeedDownloaded.objects.filter(re_filter=db_name, episode=None, season=regex_result.group(1)):
                return False
            FeedDownloaded.objects.create(re_filter=db_name, episode=regex_result.group(2),
                                          season=regex_result.group(1))
            return True
    regex_result = re.match('.*%s.*S(\d\d)' % db_name, title)
    if regex_result:
        try:
            FeedDownloaded.objects.get(re_filter=db_name, episode=None, season=regex_result.group(1))
            return False
        except ObjectDoesNotExist:
            FeedDownloaded.objects.create(re_filter=db_name, episode=None, season=regex_result.group(1))
            return True
    # Unsure if the default should be to download something...
    return True


def get_dict_from_feeds(entry_feeds):
    entries_dict = {'entries': []}
    for entry in entry_feeds:
        entries_dict['entries'].append({'title': entry['title'], 'link': entry['link']})
    return entries_dict


def match(entry, filters):
    # Have to import it locally to prevent circular import errors.
    from mii_rss.tasks import logger
    # The logger could also be a report so it has to be the same.
    for re_filter in filters:
        if re.search(re_filter, entry['title']):
            logger.info('Filter is matching: %s <-> %s' % (re_filter, entry['title']))
            return True, re_filter
    return False, None