import mock
from django.test import TestCase, override_settings
from fake_filesystem_unittest import TestCase as FakeFsTestCase
from mii_rss.logic import already_exists, match, get_or_create_downloading_object, get_dict_from_feeds
from mii_rss.models import FeedDownloaded, FeedEntries
from mii_rss.tasks import check_feed_and_download_torrents
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

        assert not match(entry, filters)[0]

        entry = {
            'title': 'homeland s04e09 theres something else going on 720p hdtv dd5 1 mpeg2-topkek  [no rar]'
        }

        assert match(entry, filters)[0]

        entry = {
            'title': 'better call saul s01e01 720p hdtv x264-killers [no rar]'
        }
        assert match(entry, filters)[0]

    def test_episode_does_not_already_exist(self):
        db_name = 'Saitama'
        title = 'Saitama.S01E01.mkv'
        assert not already_exists(db_name, title)

    def test_episode_already_exists(self):
        serie = Serie.objects.create(name='Saitama')
        season = Season.objects.create(number=1, serie=serie)
        Episode.objects.create(number=1, season=season, file_size=100, file_path='')
        db_name = 'Saitama'
        title = 'Saitama.S01E01.mkv'
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


@override_settings(RSS_FILTERS={'non_matching': 'test_entry'}, TORRENT_WATCHED_FOLDER='/')
class TestTask(FakeFsTestCase, TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    @mock.patch('mii_rss.tasks.logger')
    @mock.patch('mii_rss.tasks.feedparser')
    def test_task_feed_error(self, feedparser, logger):
        feedparser.parse.return_value = {'status': 500}
        check_feed_and_download_torrents()
        assert logger.error.called

    @mock.patch('mii_rss.tasks.feedparser')
    def test_task_feed_dumping_entries(self, feedparser):
        feedparser.parse.return_value = {'status': 200, 'entries': []}
        check_feed_and_download_torrents()
        assert FeedEntries.objects.all()

    @mock.patch('mii_rss.tasks.feedparser')
    def test_task_feed(self, feedparser):
        feedparser.parse.return_value = {'status': 200, 'entries': [{'title': 'arrow', 'link': None}]}
        check_feed_and_download_torrents()

    @mock.patch('mii_rss.tasks.urllib')
    @mock.patch('mii_rss.tasks.feedparser')
    def test_task_feed_matching_already_exist(self, feedparser, urllib):
        self.fs.CreateFile('/test.torrent')
        feedparser.parse.return_value = {'status': 200,
                                         'entries': [{'title': 'non_matching', 'link': '/test.torrent?'}]
                                         }
        check_feed_and_download_torrents()
        assert not urllib.urlretrieve.called

    @mock.patch('mii_rss.tasks.urllib')
    @mock.patch('mii_rss.tasks.feedparser')
    def test_task_feed_matching_downloading(self, feedparser, urllib):
        feedparser.parse.return_value = {'status': 200,
                                         'entries': [{'title': 'non_matching', 'link': '/test.torrent?'}]
                                         }
        check_feed_and_download_torrents()
        assert urllib.urlretrieve.called


