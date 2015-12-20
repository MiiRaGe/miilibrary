# -*- coding: utf-8 -*-

import logging
import mock
import os
import tempfile

from django.test import override_settings, TestCase

from mii_indexer.indexer import dict_merge_list_extend
from mii_indexer.models import MovieRelation
from mii_indexer.models import MovieTagging, Person
from mii_sorter.models import Movie, Episode, Serie, Season, get_serie_episode, WhatsNew
from mii_sorter.sorter import is_serie, apply_custom_renaming, change_token_to_dot, format_serie_name, compare, \
    letter_coverage, rename_serie, get_episode, get_quality, get_info, get_best_match
from utils.base import TestMiilibrary

logger = logging.getLogger(__name__)


@mock.patch('mii_unpacker.unpacker.link', new=mock.MagicMock(side_effect=AttributeError))
class TestMain(TestMiilibrary):
    def test_unpack(self):
        logger.info("== Testing doUnpack ==")
        self.mnl.unpack()
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

    def test_sort(self):
        self._fill_data()
        self.mnl.sort()
        self.assertEqual(Movie.objects.all().count(), 2)
        self.assertEqual(Episode.objects.all().count(), 1)
        self.assertEqual(WhatsNew.objects.all().count(), 3)

    def test_sort_movie(self):
        self._fill_data()
        self.mnl.sort()
        self.assertIsNotNone(Movie.objects.get(title='Thor', year=2011))
        self.assertIsNotNone(Movie.objects.get(title='Thor- The Dark World', year=2013))

        self.assertEqual(len(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All'))), 2)
        self.assertIn('Thor- The Dark World (2013)', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))
        self.assertIn('Thor (2011)', os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))

    def test_sort_serie(self):
        self._fill_data()
        self.mnl.sort()
        self.assertIsNotNone(get_serie_episode('The Big Bank Theory', 1, 1))
        self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv',
                      os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today')))
        self.assertEqual(len(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'TVSeries', 'The Big Bank Theory', 'Season 1'))), 1)

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

    def test_main(self):
        logger.info("== Testing doUnpack ==")
        self.mnl.unpack()
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

        self.mnl.sort()

        self.assertEqual(Movie.objects.all().count(), 2)

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

        self.assertEqual(MovieTagging.objects.count(), 0)
        self.assertEqual(MovieRelation.objects.count(), 0)
        self.assertEqual(Person.objects.count(), 0)
        self.mnl.index()
        self.assertEqual(MovieTagging.objects.count(), 7)
        self.assertEqual(MovieRelation.objects.count(), 33)
        self.assertEqual(Person.objects.count(), 22)

    @override_settings(DUMP_INDEX_JSON_FILE_NAME='data.json')
    def test_json_dump(self):
        logger.info("== Testing doUnpack ==")
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


@override_settings(CUSTOM_RENAMING={'BARNABY': 'Barbie'})
class TestSorter(TestCase):
    def test_is_serie(self):
        assert is_serie('downton_abbey.5x08.720p_hdtv_x264-fov.mkv')
        assert not is_serie('23name,asefjklS03esfsjkdlS05E1')
        assert is_serie('23name,asefjklS03esfsjkdlS05e10')

    def test_customer_renaming(self):
        serie1 = 'my name is BARNABYS S03E02'
        serie2 = 'my name is barnabyBARNABYS S03E02'
        serie3 = 'my name is BARNABS S03E02'
        serie4 = 'my name is barnabys S03E02'

        assert serie1 != apply_custom_renaming(serie1)
        assert serie2 != apply_custom_renaming(serie2)
        assert serie3 == apply_custom_renaming(serie3)
        assert apply_custom_renaming(serie1) == apply_custom_renaming(serie4)

    def test_format_serie_name(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/....?'
        assert 'The Walking Dead' == format_serie_name(serie_name1)

    def test_change_token_to_dot(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/.'
        assert 'The.Walking.Dead.' == change_token_to_dot(serie_name1)

    def test_compare(self):
        api_result = {
            'MovieName': 'Dragons.defenders.of.berk',
            'MovieKind': 'movie'
        }

        serie1 = 'Dragons.defenders.of.berk.S05e10.fap'
        assert not compare(serie1, api_result)[0]

        api_result['MovieKind'] = 'web series'
        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '9'
        assert not compare(serie1, api_result)[0]

        api_result['SeriesSeason'] = '4'
        api_result['SeriesEpisode'] = '10'
        assert not compare(serie1, api_result)[0]

        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '10'
        assert compare(serie1, api_result)[0]

        serie1 = 'Dragons.riders.of.berk.S05e10.fap'
        assert compare(serie1, api_result)[0]

        api_result['MovieName'] = 'Dragons.riders.of.berk'
        api_result['MovieKind'] = 'movie'
        api_result['MovieYear'] = '2014'
        movie1 = 'Dragons.defenders.of.berk (2014)'
        assert compare(movie1, api_result)[0]

        api_result['MovieYear'] = '2013'
        assert not compare(movie1, api_result)[0]

        movie1 = 'Dragons.defenders.of.berk'
        assert compare(movie1, api_result)[0]

    def test_letter_coverage(self):
        limit = 65
        str1 = 'Dragons riders of berk'

        str2 = 'Dragons defenders of berk'
        assert letter_coverage(str1, str2) >= limit

        str1 = 'Anchorman 2 The Legend Continues'
        str2 = 'Anchorman The Legend of Ron Burgundy'
        assert letter_coverage(str1, str2) <= limit

        str1 = 'How to Train Your Dragon'
        str2 = 'House of Flying Daggers'
        assert letter_coverage(str1, str2) <= limit

        str1 = 'friends.'
        str2 = 'New Girl'
        assert letter_coverage(str1, str2) <= limit

    def test_rename_serie(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/..25x15..?'
        assert 'The.Walking.Dead.S25E15.' == rename_serie(serie_name1)

    def test_get_episode(self):
        tmp_dir = tempfile.mkdtemp()

        f1 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E04.mkv')
        f2 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E02.mkv')
        f3 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E05.mkv')

        assert not get_episode(tmp_dir, 'useless arg', '01')
        assert get_episode(tmp_dir, 'useless arg', '02')
        assert not get_episode(tmp_dir, 'useless arg', '03')

    def test_get_quality(self):
        name = 'serie de malade 720p 1080p DTS AC3 BLU-ray webrip'
        quality = get_quality(name)

        self.assertIn('720p', quality)
        self.assertIn('DTS', quality)
        self.assertIn('AC3', quality)
        self.assertIn('BluRay', quality)
        self.assertIn('WebRIP', quality)

        self.assertNotIn('1080p', quality)
        self.assertNotIn('Web-RIP', quality)

    def test_get_info(self):
        name = 'The.Matrix.2001.mkv'
        res = get_info(name)
        self.assertEqual(res['title'], 'The Matrix')
        self.assertEqual(res['year'], '2001')

        name = 'Hancock.(2004).mkv'
        res = get_info(name)
        self.assertEqual(res['title'], 'Hancock')
        self.assertEqual(res['year'], '2004')

        name = '2012.(2007).mkv'
        res = get_info(name)
        self.assertEqual(res['title'], '2012')
        self.assertEqual(res['year'], '2007')

        name = '2012.720p.mkv'
        res = get_info(name)
        self.assertEqual(res['title'], '2012')
        self.assertIsNone(res.get('year'))

        name = 'Iron Man 3.mkv'
        res = get_info(name)
        self.assertEqual(res['title'], 'Iron Man 3')

    def test_get_best_match(self):
        data = [{
                    'SeriesEpisode': '3',
                    'MovieKind': 'episode', 'SeriesSeason': '5',
                    'MovieName': '"Drop Dead Diva" Surrogates',
                    'MovieYear': '2013'},
                {
                    'SeriesEpisode': '3',
                    'MovieKind': 'episode', 'SeriesSeason': '5',
                    'MovieName': '"The Walking Dead" Four Walls and a Roof',
                    'MovieYear': '2014'}]

        serie = 'The.Walking.Dead.S05E03.mkv'
        self.assertEqual(get_best_match(data, serie)['MovieName'],
                         '"The Walking Dead" Four Walls and a Roof')

        data = [
            {"SeriesEpisode": "1", "MovieKind": "episode", "SeriesSeason": "5",
             "MovieName": "\"Waking the Dead\" Towers of Silence: Part 1",
             "MovieYear": "2005"},
            {"SeriesEpisode": "1", "MovieKind": "episode", "SeriesSeason": "5",
             "MovieName": "\"The Walking Dead\" No Sanctuary",
             "MovieYear": "2014"},
            {"SeriesEpisode": "1", "MovieKind": "episode", "SeriesSeason": "5",
             "MovieName": "\"Waking the Dead\" Towers of Silence: Part 1",
             "MovieYear": "2005"}, ]

        serie = 'The.Walking.Dead.S05E01.mkv'

        self.assertEqual(get_best_match(data, serie)['MovieName'],
                         '"The Walking Dead" No Sanctuary')


class TestIndexer(TestCase):
    def test_dict_merge(self):
        d1 = {'A': {'B': ['AB'],
                    'C': ['AC']}}
        d2 = {'A': {'B': ['AB'],
                    'D': ['PD'],
                    'E': {'F': ['AEF']}}}
        merged_dict = dict_merge_list_extend(d1, d2)
        self.assertDictEqual(merged_dict, {'A': {'C': ['AC'], 'B': ['AB', 'AB'], 'E': {'F': ['AEF']}, 'D': ['PD']}})

    def test_dict_merge_empty(self):
        d2 = {'--': ['Thor (2011) [720p]'], 'T': {'--': ['Thor (2011) [720p]'], 'H': {'--': ['Thor (2011) [720p]'],
                                                                                      'O': {
                                                                                          '--': ['Thor (2011) [720p]'],
                                                                                          'R': {
                                                                                              '--': [
                                                                                                  'Thor (2011) [720p]']}}}}}
        merged_dict = dict_merge_list_extend({}, d2)
        self.assertDictEqual(d2, merged_dict)
        merged_dict = dict_merge_list_extend(d2, {})
        self.assertDictEqual(d2, merged_dict)