# -*- coding: utf-8 -*-

import logging
import mock
import os

from datetime import timedelta
from django.test import override_settings
from django.utils import timezone

from mii_indexer.models import MovieRelation
from mii_indexer.models import MovieTagging, Person
from mii_sorter.models import Movie, Episode, Serie, Season, get_serie_episode, WhatsNew
from utils.base import TestMiilibrary

logger = logging.getLogger(__name__)


@mock.patch('mii_unpacker.unpacker.link', new=mock.MagicMock(side_effect=AttributeError))
class TestMain(TestMiilibrary):
    def test_unpack(self):
        logger.info("== Testing doUnpack ==")
        self.mnl.unpack()
        assert len(os.listdir(self.DESTINATION_FOLDER + '/data')) == 5

    def test_sort(self):
        self._fill_data()
        self.mnl.sort()
        assert Movie.objects.all().count() == 2
        assert Episode.objects.all().count() == 1
        assert WhatsNew.objects.all().count() == 3

    def test_sort_movie(self):
        self._fill_data()
        self.mnl.sort()
        self.assertIsNotNone(Movie.objects.get(title='Thor', year=2011))
        self.assertIsNotNone(Movie.objects.get(title='Thor- The Dark World', year=2013))

        assert len(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All'))) == 2
        self.assertIn('Thor- The Dark World (2013)', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))
        self.assertIn('Thor (2011)', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))

    def test_sort_serie(self):
        self._fill_data()
        self.mnl.sort()
        self.assertIsNotNone(get_serie_episode('The Big Bank Theory', 1, 1))
        self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv',
                      os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))
        assert len(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'TVSeries', 'The Big Bank Theory', 'Season 1'))) == 1

    def test_new(self):
        tday = timezone.now()
        for i in range(0, 70):
            WhatsNew.objects.create(path=self.DESTINATION_FOLDER, date=tday - timedelta(days=i), name=i)
        self.mnl.sorter.update_new()
        expected = ['1 month(s) ago', '1 week(s) ago', '2 day(s) ago', '2 week(s) ago', '3 day(s) ago', '3 week(s) ago',
                    '4 day(s) ago', '4 week(s) ago', '5 day(s) ago', '6 day(s) ago', 'Today', 'Yesterday']
        assert sorted(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New'))) == sorted(expected)

    def test_index(self):
        self._fill_movie()
        movie1 = Movie.objects.create(title='Thor', year='2011', imdb_id='0800369', file_size=10)
        movie1.file_path = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor (2011)', 'Thor.(2011).720p.mkv')
        movie1.save()
        movie2 = Movie.objects.create(title='Thor- The Dark World', year='2013', imdb_id='1981115', file_size=10)
        movie2.file_path = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor- The Dark World (2013)', 'Thor-.The.Dark.World.(2013).720p.mkv')
        movie2.save()
        self.mnl.index()
        self.assertEqual(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Years')),
                         ['2011', '2013'])
        self.assertEqual(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Genres')),
                         ['Action', 'Adventure', 'Bullshit', 'Fantasy', 'London', 'Romance'])
        self.assertEqual(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Directors')),
                         ['Alan Taylor', 'Joss Whedon', 'Kenneth Branagh'])
        self.assertIn('Chris Hemsworth', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Actors')))
        self.assertIn('Natalie Portman', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Actors')))
        self.assertIn('Tom Hiddleston', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Actors')))
        self.assertEqual(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Ratings')),
                         ['7.0', '9.5'])
        self.assertEqual(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index', 'Ratings', '7.0')), ['Thor (2011)'])

    def test_unpack_sort_index(self):
        self.mnl.unpack()
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

        self.mnl.sort()

        assert Movie.objects.all().count() == 2

        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')), 2)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')), 1)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')), 1)

        self.assertIsNotNone(Episode.objects.get(number=1))
        self.assertIsNotNone(Season.objects.get(number=1))
        self.assertIsNotNone(Serie.objects.get(name='The Big Bank Theory'))

        self.assertIn('The Big Bank Theory', os.listdir(self.DESTINATION_FOLDER + '/TVSeries'))
        self.assertIn('Season 1', os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory'))
        self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv',
                      os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory/Season 1'))

        assert MovieTagging.objects.count() == 0
        assert MovieRelation.objects.count() == 0
        assert Person.objects.count() == 0
        self.mnl.index()
        assert MovieTagging.objects.count() == 7
        assert MovieRelation.objects.count() == 33
        assert Person.objects.count() == 22

    @override_settings(DUMP_INDEX_JSON_FILE_NAME='data.json')
    def test_json_dump(self):
        self.mnl.unpack()
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

        self.mnl.sort()

        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')), 2)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')), 1)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')), 1)

        self.assertIn('The Big Bank Theory', os.listdir(self.DESTINATION_FOLDER + '/TVSeries'))
        self.assertIn('Season 1', os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory'))
        self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv',
                      os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory/Season 1'))

        self.mnl.index()
        self.assertTrue(os.path.exists(self.DESTINATION_FOLDER + '/data.json'))

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

