import mock

from django.test import TestCase

from mii_indexer.factories import MovieRelationFactory, MovieTaggingFactory
from mii_interface.factories import ReportFactory
from mii_sorter.factories import EpisodeFactory


class TestViews(TestCase):
    def setUp(self):
        MovieTaggingFactory.create()
        MovieTaggingFactory.create()
        MovieTaggingFactory.create()
        MovieRelationFactory.create()
        MovieRelationFactory.create()
        MovieRelationFactory.create()
        MovieRelationFactory.create()
        EpisodeFactory.create()
        EpisodeFactory.create()
        EpisodeFactory.create()
        EpisodeFactory.create()
        EpisodeFactory.create()
        ReportFactory.create()
        ReportFactory.create()
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

    @mock.patch('mii_interface.views.index_movies')
    @mock.patch('mii_interface.views.unpack')
    @mock.patch('mii_interface.views.sort')
    def test_rpc_index(self, sort, unpack, index):
        response = self.client.get('/rpc/unpack_sort_index')
        assert response.status_code == 200
        assert index.si.called
        assert unpack.si.called
        assert sort.si.called
