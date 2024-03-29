import os

import mock

from django.test import TestCase
from django.test import override_settings
from pyfakefs.fake_filesystem_unittest import TestCase as FSTestCase

from mii_common import tools
from mii_indexer.factories import MovieRelationFactory, MovieTaggingFactory
from mii_interface.factories import ReportFactory
from mii_interface.views import discrepancies
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

    @mock.patch('mii_interface.views.remote_play')
    def test_play(self, remote_play):
        self.client.post('/play', data={'episode_id': self.episode.id})
        remote_play.assert_called_with(self.episode.file_path)


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
        serie_dir = tools.make_dir(os.path.join(dest_dir, 'Series'))
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

    @mock.patch('mii_interface.views.render')
    def test_discrepancies(self, render):
        request = mock.MagicMock()
        discrepancies(request)
        render.assert_called_with(
            request,
            mock.ANY,
            {
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
                'episodes_discrepancy': [{'title': 'Episode object (2)', 'file_path': '{destination_dir}serie_13.mkv', 'id': 2}],
                'serie_folder_discrepancy': [
                    {'name': 'Serie1',
                     'folder_path': '/processed/Series/Serie1',
                     'seasons': [{
                         'number': '1',
                         'folder_path': '/processed/Series/Serie1/Season 1',
                         'episodes': [
                             {'number': 1,
                              'file_path': '/processed/Series/Serie1/Season 1/serie.name.s01e01.mkv',
                              'file_size': 5}
                         ]
                     }
                     ]
                     }
                ],
            }
        )

    @mock.patch('mii_interface.views.render')
    def test_discrepancies_fixing(self, render):
        fixing_request = mock.MagicMock()
        fixing_request.method = 'POST'
        discrepancies(fixing_request)
        request = mock.MagicMock()
        request.method = 'GET'
        discrepancies(request)
        render.assert_called_with(
            request,
            mock.ANY,
            {
                'movie_discrepancy': [],
                'folder_discrepancy': [],
                'serie_folder_discrepancy': [],
                'episodes_discrepancy': [],
                'seasons_discrepancy': [],
                'series_discrepancy': [],
            }
        )
