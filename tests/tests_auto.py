# -*- coding: utf-8 -*-

import logging
import os
import shutil
import tempfile
import unittest

from mock import patch

# Patch the logger file before import any custom file

abs_log_file = '%s/test_log.LOG' % os.path.dirname(__file__)
try:
    os.remove(abs_log_file)
except OSError:
    pass
test_handler = logging.FileHandler(abs_log_file)
test_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
logger = logging.getLogger('NAS')
logger.addHandler(test_handler)

import settings
# Override some settings now before initialising anything else
settings.SOURCE_FOLDER = '%s/test_input/' % os.path.dirname(__file__)
settings.DESTINATION_FOLDER = '%s/test_output/' % os.path.dirname(__file__)
settings.MONGO_DB_NAME += '_test'
settings.MYSQL_NAME += '_test'
from middleware.mii_sql import db, TABLE_LIST

if 'test' in db.database:
    db.drop_tables(TABLE_LIST,
                   cascade=True)
    db.create_tables(TABLE_LIST,
                     safe=True)

from mock_osdb import *
from mock_tmdb import *
from movieinfo.opensubtitle_wrapper import OpenSubtitleWrapper
from movieinfo.the_movie_db_wrapper import TheMovieDBWrapper
from indexer.Indexer import dict_merge_list_extend

try:
    raise WindowsError
except NameError:
    WindowsError = None
except Exception:
    pass


class TestMain(unittest.TestCase):
    def setUp(self):
        logger.info("*** Building environment ***")

        self.SOURCE_FOLDER = '%s/test_input/' % os.path.dirname(__file__)
        self.DESTINATION_FOLDER = '%s/test_output/' % os.path.dirname(__file__)

        abs_data = '%s/test_data/' % os.path.dirname(__file__)
        logger.info("\t ** Moving Files **")
        try:
            for media_file in os.listdir(abs_data):
                logger.info("\t\t * Moving: %s *" % media_file)
                shutil.copy(os.path.join(abs_data, media_file), os.path.join(self.SOURCE_FOLDER, media_file))
        except WindowsError:
            logger.info("\t\t * No data to move... tests are void **")
        logger.info("*** Environment Builded ***")

    def tearDown(self):
        import tools

        logger.info("*** Tearing down environment ***")
        abs_input = self.SOURCE_FOLDER
        logger.info("\t ** Cleaning input Files **")
        try:
            tools.cleanup_rec(abs_input)
        except WindowsError:
            logger.info("\t\t * No data to move... tests are void **")

        logger.info("\t ** Cleaning output directory **")
        abs_output = self.DESTINATION_FOLDER
        try:
            tools.cleanup_rec(abs_output)
        except WindowsError:
            logger.info("\t\t * No data to move... tests are void **")

        logger.info("*** Environment Torn Down***")


    @patch.multiple(OpenSubtitleWrapper,
                    get_movie_names=mock_get_movie_names,
                    get_subtitles=mock_get_movie_names,
                    get_movie_names2=mock_get_movie_names2,
                    get_imdb_information=mock_get_imdb_information)
    @patch.multiple(TheMovieDBWrapper,
                    get_movie_name=mock_get_movie_name,
                    get_movie_imdb_id=mock_get_movie_imdb_id)
    def test_main(self):
        with patch.multiple(settings,
                            SOURCE_FOLDER=self.SOURCE_FOLDER,
                            DESTINATION_FOLDER=self.DESTINATION_FOLDER,
                            MINIMUM_SIZE=0.2):
            import tools
            from miinaslibrary import MiiNASLibrary

            logger.info("== Testing validate_settings ==")

            self.assertTrue(tools.validate_settings())

            logger.info("== Testing doUnpack ==")
            mnl = MiiNASLibrary()
            mnl.unpack()
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

            mnl.sort()

            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')), 2)
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')), 2)
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')),
                             2)

            self.assertIn('.IMDB_ID_tt0800369', os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]'))
            self.assertIn('.IMDB_ID_tt1981115',
                          os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)'))

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


class TestSorter(unittest.TestCase):
    def test_is_serie(self):
        from sorter.sorter import is_serie

        self.assertFalse(is_serie('23name,asefjklS03esfsjkdlS05E1'))
        self.assertTrue(is_serie('23name,asefjklS03esfsjkdlS05e10'))

    def test_customer_renaming(self):
        from sorter.sorter import apply_custom_renaming

        settings.CUSTOM_RENAMING = {
            'BARNABY': 'Barbie'
        }

        serie1 = 'my name is BARNABYS S03E02'
        serie2 = 'my name is barnabyBARNABYS S03E02'
        serie3 = 'my name is BARNABS S03E02'
        serie4 = 'my name is barnabys S03E02'

        self.assertNotEqual(serie1, apply_custom_renaming(serie1))
        self.assertNotEqual(serie2, apply_custom_renaming(serie2))
        self.assertEqual(serie3, apply_custom_renaming(serie3))
        self.assertEqual(apply_custom_renaming(serie1), apply_custom_renaming(serie4))


    def test_format_serie_name(self):
        from sorter.sorter import format_serie_name

        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/....?'
        self.assertEqual('The Walking Dead', format_serie_name(serie_name1))

    def test_change_token_to_dot(self):
        from sorter.sorter import change_token_to_dot

        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/.'
        self.assertEqual('The.Walking.Dead.', change_token_to_dot(serie_name1))

    def test_compare(self):
        from sorter.sorter import compare

        api_result = {
            'MovieName': 'Dragons.defenders.of.berk',
            'MovieKind': 'movie'
        }

        serie1 = 'Dragons.defenders.of.berk.S05e10.fap'
        self.assertFalse(compare(serie1, api_result)[0])

        api_result['MovieKind'] = 'web series'
        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '9'
        self.assertFalse(compare(serie1, api_result)[0])

        api_result['SeriesSeason'] = '4'
        api_result['SeriesEpisode'] = '10'
        self.assertFalse(compare(serie1, api_result)[0])

        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '10'
        self.assertTrue(compare(serie1, api_result)[0])

        serie1 = 'Dragons.riders.of.berk.S05e10.fap'
        self.assertTrue(compare(serie1, api_result)[0])

        api_result['MovieName'] = 'Dragons.riders.of.berk'
        api_result['MovieKind'] = 'movie'
        api_result['MovieYear'] = '2014'
        movie1 = 'Dragons.defenders.of.berk (2014)'
        self.assertTrue(compare(movie1, api_result)[0])

        api_result['MovieYear'] = '2013'
        self.assertFalse(compare(movie1, api_result)[0])

        movie1 = 'Dragons.defenders.of.berk'
        self.assertTrue(compare(movie1, api_result)[0])

    def test_letter_coverage(self):
        from sorter.sorter import letter_coverage

        limit = 65
        str1 = 'Dragons riders of berk'

        str2 = 'Dragons defenders of berk'
        self.assertGreaterEqual(letter_coverage(str1, str2), limit)

        str1 = 'Anchorman 2 The Legend Continues'
        str2 = 'Anchorman The Legend of Ron Burgundy'
        self.assertLessEqual(letter_coverage(str1, str2), limit)

        str1 = 'How to Train Your Dragon'
        str2 = 'House of Flying Daggers'
        self.assertLessEqual(letter_coverage(str1, str2), limit)

        str1 = 'friends.'
        str2 = 'New Girl'
        self.assertLessEqual(letter_coverage(str1, str2), limit)

    def test_rename_serie(self):
        from sorter.sorter import rename_serie

        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/..25x15..?'
        self.assertEqual('The.Walking.Dead.S25E15.', rename_serie(serie_name1))

    def test_get_episode(self):
        from sorter.sorter import get_episode

        tmp_dir = tempfile.mkdtemp()

        f1 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E04.mkv')
        f2 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E02.mkv')
        f3 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E05.mkv')

        self.assertIsNone(get_episode(tmp_dir, 'useless arg', '01'))
        self.assertIsNotNone(get_episode(tmp_dir, 'useless arg', '02'))
        self.assertIsNone(get_episode(tmp_dir, 'useless arg', '03'))

    def test_get_quality(self):
        from sorter.sorter import get_quality

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
        from sorter.sorter import get_info

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
        from sorter.sorter import get_best_match

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


class TestIndexer(unittest.TestCase):
    def test_dict_merge(self):
        d1 = {'A': {'B': ['AB'],
                    'C': ['AC']}}
        d2 = {'A': {'B': ['AB'],
                    'D': ['PD'],
                    'E': {'F': ['AEF']}}}
        merged_dict = dict_merge_list_extend(d1, d2)
        self.assertDictEqual(merged_dict, {'A': {'C': ['AC'], 'B': ['AB', 'AB'], 'E': {'F': ['AEF', 'AEF']}, 'D': ['PD', 'PD']}})

    def test_dict_merge_empty(self):
        d2 = {'--': ['Thor (2011) [720p]'], 'T': {'--': ['Thor (2011) [720p]'], 'H': {'--': ['Thor (2011) [720p]'], 'O': {'--': ['Thor (2011) [720p]'], 'R': {'--': ['Thor (2011) [720p]']}}}}}
        merged_dict = dict_merge_list_extend({}, d2)
        self.assertDictEqual(d2, merged_dict)
        merged_dict = dict_merge_list_extend(d2, {})
        self.assertDictEqual(d2, merged_dict)