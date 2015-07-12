# -*- coding: utf-8 -*-

import logging
import os
import shutil
import tempfile
import mock

from django.conf import settings
from django.test import override_settings, TestCase

from settings.utils import relative
from mock_osdb import *
from mock_tmdb import *
from mii_indexer.indexer import dict_merge_list_extend
from mii_sorter.sorter import is_serie, apply_custom_renaming, change_token_to_dot, format_serie_name, compare, \
    letter_coverage, rename_serie, get_episode, get_quality, get_info, get_best_match
from mii_common import tools
from miinaslibrary import MiiNASLibrary

logger = logging.getLogger(__name__)

mii_osdb_mock = mock.MagicMock()
mii_osdb_mock.get_movie_name = mock_get_movie_names2
mii_osdb_mock.get_imdb_information = mock_get_imdb_information
mii_osdb_mock.get_movie_names = mock_get_movie_names
mii_osdb_mock.get_subtitles = mock_get_movie_names

mii_tmdb_mock = mock.MagicMock()
mii_tmdb_mock.get_movie_name = mock_get_movie_name
mii_tmdb_mock.get_movie_imdb_id = mock_get_movie_imdb_id


@override_settings(MINIMUM_SIZE=0.2, NAS_IP=None, NAS_USERNAME=None)
@mock.patch('mii_indexer.indexer.Indexer.mii_osdb', new=mii_osdb_mock)
@mock.patch('mii_sorter.sorter.Sorter.mii_tmdb', new=mii_tmdb_mock)
@mock.patch('mii_sorter.sorter.Sorter.mii_osdb', new=mii_osdb_mock)
class TestMain(TestCase):
    def setUp(self):
        logger.info("*** Building environment ***")

        self.SOURCE_FOLDER = settings.SOURCE_FOLDER
        self.DESTINATION_FOLDER = settings.DESTINATION_FOLDER

        abs_data = relative('tests/test_data/')

        logger.info("\t ** Moving Files **")
        for media_file in os.listdir(abs_data):
            logger.info("\t\t * Moving: %s *" % media_file)
            shutil.copy(os.path.join(abs_data, media_file), os.path.join(self.SOURCE_FOLDER, media_file))
        logger.info("*** Environment Builded ***")

    def tearDown(self):
        logger.info("*** Tearing down environment ***")
        abs_input = self.SOURCE_FOLDER
        logger.info("\t ** Cleaning input Files **")
        tools.cleanup_rec(abs_input)

        logger.info("\t ** Cleaning output directory **")
        abs_output = self.DESTINATION_FOLDER
        tools.cleanup_rec(abs_output)
        logger.info("*** Environment Torn Down***")

    def test_main(self):
        logger.info("== Testing validate_settings ==")

        self.assertTrue(tools.validate_settings())

        logger.info("== Testing doUnpack ==")
        mnl = MiiNASLibrary()
        mnl.unpack()
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

        mnl.sort()

        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')), 2)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')), 1)
        self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')), 1)

        self.assertIn('The Big Bank Theory', os.listdir(self.DESTINATION_FOLDER + '/TVSeries'))
        self.assertIn('Season 1', os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory'))
        self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv',
                      os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory/Season 1'))

        mnl.index()
        # TODO : Add test for assertions on sorted stuff
        # TODO : Add test for opensubtitle (get real data from production and mock the result with a fake hash)


        # Test for behaviour with duplicates
        self.setUp()

        mnl.unpack()
        mnl.sort()
        mnl.index()

        tools.print_rec(self.DESTINATION_FOLDER, 0)

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