from django.test import TestCase

from mii_rss.logic import already_exists, match, get_or_create_downloading_object, get_dict_from_feeds
from mii_rss.models import FeedDownloaded
from mii_sorter.models import Season, Episode
from mii_sorter.models import Serie


class TestRSS(TestCase):
    def test_match(self):
        entry = {
            'title': 'homeland s04e09 theres something else going on 1080i hdtv dd5 1 mpeg2-topkek  [no rar]'
        }
        filters = {
            '^homeland.*720p',
            '^star.wars.rebels.*720p',
            '^better.call.saul.*720p'
        }

        self.assertFalse(match(entry, filters)[0])

        entry = {
            'title': 'homeland s04e09 theres something else going on 720p hdtv dd5 1 mpeg2-topkek  [no rar]'
        }

        self.assertTrue(match(entry, filters)[0])

        entry = {
            'title': 'better call saul s01e01 720p hdtv x264-killers [no rar]'
        }
        self.assertTrue(match(entry, filters)[0])

    def test_episode_does_not_already_exist(self):
        db_name = 'Saitama'
        title= 'Saitama.S01E01.mkv'
        assert not already_exists(db_name, title)

    def test_episode_already_exists(self):
        serie = Serie.objects.create(name='Saitama')
        season = Season.objects.create(number=1, serie=serie)
        Episode.objects.create(number=1, season=season, file_size=100, file_path='')
        db_name = 'Saitama'
        title= 'Saitama.S01E01.mkv'
        assert already_exists(db_name, title)

    def test_season_does_not_exist(self):
        db_name = 'Saitama'
        title = 'Saitama.S01.rar'
        assert not already_exists(db_name, title)

    def test_season_already_exists(self):
        serie = Serie.objects.create(name='Saitama')
        season = Season.objects.create(number=1, serie=serie)
        db_name = 'Saitama'
        title = 'Saitama.S01.rar'
        assert already_exists(db_name, title)

    def test_get_or_create_downloading_object_episode_create(self):
        db_name = 'Saitama'
        title = 'Saitama.S01E01.mkv'
        assert get_or_create_downloading_object(db_name, title)
        assert not get_or_create_downloading_object(db_name, title)

    def test_get_or_create_downloading_object_episode_get(self):
        db_name = 'Saitama'
        title = 'Saitama.S01E01.mkv'
        FeedDownloaded.objects.create(re_filter=db_name, episode=1, season=1)
        assert not get_or_create_downloading_object(db_name, title)

    def test_get_or_create_downloading_object_season_create(self):
        db_name = 'Saitama'
        title = 'Saitama.S01'
        assert get_or_create_downloading_object(db_name, title)
        assert not get_or_create_downloading_object(db_name, title)

    def test_get_or_create_downloading_object_season_get(self):
        db_name = 'Saitama'
        title = 'Saitama.S01'
        FeedDownloaded.objects.create(re_filter=db_name, season=1)
        assert not get_or_create_downloading_object(db_name, title)

    def test_get_or_create_downloading_object_season_get_blocks_episode(self):
        db_name = 'Saitama'
        title = 'Saitama.S01E01'
        FeedDownloaded.objects.create(re_filter=db_name, season=1)
        assert not get_or_create_downloading_object(db_name, title)

    def test_get_entry_from_feed(self):
        class Feed(object):
            def __getitem__(self, item):
                return item
        list_of_feed = [Feed() for x in range(0, 5)]
        resulting_dict = get_dict_from_feeds(list_of_feed)
        assert resulting_dict == {'entries': [{'title': 'title', 'link': 'link'} for x in range(0, 5)]}
