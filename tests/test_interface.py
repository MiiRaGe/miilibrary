import os

import mock

from django.test import TestCase
from django.test import override_settings
from django.utils import timezone
from pyfakefs.fake_filesystem_unittest import TestCase as FSTestCase

from mii_common import tools
from mii_indexer.factories import MovieRelationFactory, MovieTaggingFactory
from mii_interface.factories import ReportFactory
from mii_common.tools import LibraryNotMounted
from mii_interface.logic import check_library, find_discrepancies, fix_discrepancies
from mii_interface.models import Report
from mii_rss.logic import RECENT_ENTRIES, get_hashed_link, save_feed_items
from mii_rss.models import FeedItem
from mii_rating.models import QuestionAnswer, MovieQuestionSet
from mii_sorter.factories import EpisodeFactory, MovieFactory, SerieFactory, SeasonFactory
from mii_sorter.models import Movie


@override_settings(DESTINATION_FOLDER='/home/destination')
class TestViews(TestCase):
    @classmethod
    def setUpTestData(cls):
        MovieTaggingFactory.create_batch(3)
        MovieRelationFactory.create_batch(5)
        EpisodeFactory.create_batch(6)
        ReportFactory.create_batch(5)
        cls.episode = EpisodeFactory.create()
        cls.report = ReportFactory.create()

    def test_index(self):
        assert self.client.get('/').status_code == 200

    def test_movies(self):
        assert self.client.get('/movies').status_code == 200

    def test_series(self):
        assert self.client.get('/series').status_code == 200

    def test_rate(self):
        assert self.client.get('/rate').status_code == 200

    def test_reports(self):
        assert self.client.get('/reports').status_code == 200

    def test_report(self):
        assert self.client.get('/report/%s/' %
                               self.report.id).status_code == 200

    def test_report_missing(self):
        assert self.client.get('/report/39202390/').status_code == 200

    @mock.patch('mii_unpacker.views.unpack')
    def test_rpc_unpack(self, unpack):
        response = self.client.get('/rpc/unpack')
        assert response.status_code == 200
        assert unpack.delay.called

    @mock.patch('mii_sorter.views.sort')
    def test_rpc_sort(self, sort):
        response = self.client.get('/rpc/sort')
        assert response.status_code == 200
        assert sort.delay.called

    @mock.patch('mii_indexer.views.index_movies')
    def test_rpc_index(self, index):
        response = self.client.get('/rpc/index')
        assert response.status_code == 200
        assert index.delay.called

    @mock.patch('mii_rss.views.recheck_feed_and_download_torrents')
    def test_rpc_rerss(self, index):
        response = self.client.get('/rpc/recheck_rss')
        assert response.status_code == 200
        assert index.delay.called

    @mock.patch('mii_rss.views.check_feed_and_download_torrents')
    def test_rpc_rss(self, rss):
        response = self.client.get('/rpc/rss')
        assert response.status_code == 200
        assert rss.delay.called

    @mock.patch('mii_interface.views.index_movies')
    @mock.patch('mii_interface.views.unpack')
    @mock.patch('mii_interface.views.sort')
    def test_rpc_index(self, sort, unpack, index):
        response = self.client.get('/rpc/unpack_sort_index')
        assert response.status_code == 200
        assert index.si.called
        assert unpack.si.called
        assert sort.si.called

    def test_mii_rating(self):
        movie = MovieFactory.create(seen=None)
        data = {
            'action': 'not_seen',
            'movie_id': movie.id
        }
        response = self.client.post('/rate', data=data)
        assert Movie.objects.get(id=movie.id).seen is False
        assert response.status_code == 200


@override_settings(DESTINATION_FOLDER='/home/destination')
class TestMiiRating(TestCase):
    def test_mii_rating_save_question(self):
        movie = MovieFactory.create(seen=None)
        data = {
            'action': 'save_movie',
            'movie_id': movie.id,
            'overall': ['9.4'],
        }
        response = self.client.post('/rate', data=data)
        assert MovieQuestionSet.objects.get(movie_id=movie.id)
        assert QuestionAnswer.objects.get(question_type='overall')
        assert response.status_code == 200

    def test_mii_rating_missing_movie(self):
        response = self.client.get('/rate?movie_id=1')
        assert response.status_code == 200

    def test_rate_with_info(self):
        movie = MovieFactory.create(seen=None)
        MovieRelationFactory.create_batch(5, movie=movie)
        MovieTaggingFactory.create_batch(5, movie=movie)
        response = self.client.get('/rate')
        assert response.status_code == 200


class TestGetTorrents(TestCase):
    def feed(self, *titles):
        save_feed_items([{'title': title, 'link': 'http://tracker/%s.torrent?passkey=secret' % title}
                         for title in titles])

    def test_lists_entries_once_newest_first(self):
        self.feed('old', 'both')
        self.feed('both', 'new')
        response = self.client.get('/get')
        assert response.status_code == 200
        assert [entry.title for entry in response.context['entries']] == ['new', 'old', 'both']
        assert b'passkey' not in response.content

    def test_only_recent_entries(self):
        self.feed('too_old')
        self.feed(*['recent%s' % number for number in range(RECENT_ENTRIES)])
        titles = [entry.title for entry in self.client.get('/get').context['entries']]
        assert len(titles) == RECENT_ENTRIES
        assert 'too_old' not in titles

    def test_added_entry_has_no_button(self):
        self.feed('wanted', 'other')
        FeedItem.objects.filter(title='wanted').update(added=timezone.now())
        response = self.client.get('/get')
        assert response.content.count(b'type="submit"') == 1
        assert b'>Added<' in response.content

    def test_no_feeds(self):
        assert self.client.get('/get').status_code == 200

    @mock.patch('mii_interface.views.add_torrent_to_transmission')
    def test_get_adds_the_entry_to_transmission(self, add_torrent):
        self.feed('wanted', 'other')
        link = 'http://tracker/wanted.torrent?passkey=secret'
        response = self.client.post('/get', {'entry': get_hashed_link(link)}, follow=True)
        add_torrent.delay.assert_called_once_with(link)
        assert b'Queued for transmission: wanted' in response.content

    @mock.patch('mii_interface.views.add_torrent_to_transmission')
    def test_get_ignores_unknown_entries(self, add_torrent):
        self.feed('wanted')
        response = self.client.post('/get', {'entry': get_hashed_link('http://evil/x.torrent')}, follow=True)
        assert not add_torrent.delay.called
        assert b'no longer in the recent feeds' in response.content


@override_settings(DESTINATION_FOLDER='/processed/')
class TestDiscrepancies(FSTestCase, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.movie_without_path = MovieFactory.create(
            folder_path='dummy_path.mkv')
        cls.movie_with_path = MovieFactory.create(folder_path='path_exists')
        cls.movie_with_different_path = MovieFactory.create(
            title='Match', year=2000, folder_path='path_exists2')
        cls.serie_with_path = SerieFactory.create(name='Serie2')
        cls.season_with_path = SeasonFactory.create(
            serie=cls.serie_with_path, number=1)
        cls.season_without_path = SeasonFactory.create(
            serie=cls.serie_with_path, number=2)
        cls.episode_with_path = EpisodeFactory(
            season=cls.season_with_path, number=1)
        cls.episode_without_path = EpisodeFactory(
            season=cls.season_with_path, number=2)
        cls.serie_without_path = SerieFactory.create(name='Serie3')

    def setUp(self):
        self.setUpPyfakefs()
        dest_dir = tools.make_dir('/processed/')
        movie_dir = tools.make_dir(os.path.join(dest_dir, 'Movies'))
        serie_dir = tools.make_dir(os.path.join(dest_dir, 'TVSeries'))
        all_movie_dir = tools.make_dir(os.path.join(movie_dir, 'All'))
        self.title_folder = tools.make_dir(
            os.path.join(all_movie_dir, 'Title (2014)'))
        self.match_folder = tools.make_dir(
            os.path.join(all_movie_dir, 'Match (2000)'))
        self.serie1_folder = tools.make_dir(os.path.join(serie_dir, 'Serie1'))
        self.serie1_season1_folder = tools.make_dir(
            os.path.join(self.serie1_folder, 'Season 1'))
        self.serie1_season1_ep1_path = self.fs.create_file(os.path.join(
            self.serie1_season1_folder, 'serie.name.s01e01.mkv'), contents='dummy')
        self.serie2_folder = tools.make_dir(os.path.join(serie_dir, 'Serie2'))
        self.season_with_path.folder_path = tools.make_dir(
            os.path.join(self.serie2_folder, 'Season 1'))
        self.season_with_path.save()
        self.episode_with_path.file_path = os.path.join(
            self.season_with_path.folder_path, str(self.episode_with_path))
        self.episode_with_path.save()
        self.fs.create_file(self.episode_with_path.file_path, contents='dummy')
        tools.make_dir('path_exists')
        tools.make_dir('path_exists2')

    def test_discrepancies(self):
        assert find_discrepancies() == {
                'movie_discrepancy': [
                    {'title': self.movie_without_path.title, 'id': self.movie_without_path.id}],
                'folder_discrepancy': [
                    {'folder_exists': True,
                     'movie_folder_exists': True,
                     'movie_id': self.movie_with_different_path.id,
                     'folder': self.match_folder,
                     'movie_folder': self.movie_with_different_path.folder_path
                     },
                    {
                        'folder': self.title_folder
                    }
                ],
                'series_discrepancy': [{'name': 'Serie3', 'id': 2}],
                'seasons_discrepancy': [{'number': '2', 'id': 2}],
                'episodes_discrepancy': [{'title': 'Episode object (2)', 'file_path': self.episode_without_path.file_path, 'id': 2}],
                'serie_folder_discrepancy': [
                    {'name': 'Serie1',
                     'folder_path': '/processed/TVSeries/Serie1',
                     'seasons': [{
                         'number': '1',
                         'folder_path': '/processed/TVSeries/Serie1/Season 1',
                         'episodes': [
                             {'number': 1,
                              'file_path': '/processed/TVSeries/Serie1/Season 1/serie.name.s01e01.mkv',
                              'file_size': 5}
                         ]
                     }
                     ]
                     }
                ],
            }

    def test_discrepancies_fixing(self):
        fix_discrepancies()
        assert find_discrepancies() == {
            'movie_discrepancy': [],
            'folder_discrepancy': [],
            'serie_folder_discrepancy': [],
            'episodes_discrepancy': [],
            'seasons_discrepancy': [],
            'series_discrepancy': [],
        }

    @override_settings(DESTINATION_FOLDER='/not_mounted/')
    def test_discrepancies_library_not_mounted(self):
        movie_count = Movie.objects.count()
        with self.assertRaises(LibraryNotMounted):
            fix_discrepancies()
        assert Movie.objects.count() == movie_count

    @override_settings(REPORT_ENABLED=True)
    @mock.patch('mii_interface.logic.logger')
    def test_check_library_reports(self, logger):
        logger.finalize_report.return_value = 'report'
        check_library()
        assert find_discrepancies()['movie_discrepancy'] == []
        assert Report.objects.get(report_type='library_check').report_html == 'report'
