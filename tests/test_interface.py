import mock

from django.test import TestCase
from django.test import override_settings

from mii_indexer.factories import MovieRelationFactory, MovieTaggingFactory
from mii_interface.factories import ReportFactory
from mii_rating.models import QuestionAnswer, MovieQuestionSet
from mii_sorter.factories import EpisodeFactory, MovieFactory
from mii_sorter.models import Movie


@override_settings(DESTINATION_FOLDER='/home/destination')
class TestViews(TestCase):
    def setUp(self):
        MovieTaggingFactory.create_batch(3)
        MovieRelationFactory.create_batch(5)
        EpisodeFactory.create_batch(6)
        ReportFactory.create_batch(5)
        self.report = ReportFactory.create()

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
        assert self.client.get('/report/%s/' % self.report.id).status_code == 200

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
