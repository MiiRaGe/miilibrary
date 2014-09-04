__author__ = 'MiiRaGe'

import logging
import os
import shutil
import tempfile
import unittest
from mock import patch

import settings
import tools
from miinaslibrary import MiiNASLibrary
from movieinfo.opensubtitle_wrapper import OpensubtitleWrapper
from movieinfo.the_movie_db_wrapper import TheMovieDBWrapper
from mock_osdb import *
from mock_tmdb import *

from sorter.sorter import is_serie, apply_custom_renaming, format_serie_name, change_token_to_dot, \
    compare, letter_coverage, rename_serie, get_episode, get_quality, get_info

abs_log_file = '%s/test_log.LOG' % os.path.dirname(__file__)
try:
    os.remove(abs_log_file)
except OSError:
    pass
test_handler = logging.FileHandler(abs_log_file)
test_handler.setFormatter(tools.formatter)
logger = logging.getLogger('NAS')
logger.addHandler(test_handler)

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

    @patch.multiple(OpensubtitleWrapper,
                    get_movie_names=mock_get_movie_names,
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
            logger.info("== Testing validate_settings ==")
            self.assertTrue(tools.validate_settings())

            logger.info("== Testing doUnpack ==")
            mnl = MiiNASLibrary()
            mnl.doUnpack()
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 5)

            mnl.doSort()
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')), 2)
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')), 2)
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')),
                             2)

            self.assertIn('.IMDB_ID_tt0800369', os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]'))
            self.assertIn('.IMDB_ID_tt1981115', os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)'))

            self.assertIn('The Big Bank Theory', os.listdir(self.DESTINATION_FOLDER + '/TVSeries'))
            self.assertIn('Season 1', os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory'))
            self.assertIn('The.Big.Bank.Theory.S01E01.[720p].mkv', os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory/Season 1'))

            mnl.doIndex()
            #TODO : Add test for duplicate file, duplicate episode, and test unsorted
            #TODO : Add test for assertions on sorted stuff
            tools.print_rec(self.DESTINATION_FOLDER, 0) #Keep this call at the end to see the global result (move for debugging)


class TestSorter(unittest.TestCase):
    def test_is_serie(self):
        self.assertFalse(is_serie('23name,asefjklS03esfsjkdlS05E1'))
        self.assertTrue(is_serie('23name,asefjklS03esfsjkdlS05e10'))

    def test_customer_renaming(self):
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
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/....?'
        self.assertEqual('The Walking Dead', format_serie_name(serie_name1))

    def test_change_token_to_dot(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/.'
        self.assertEqual('The.Walking.Dead.', change_token_to_dot(serie_name1))

    def test_compare(self):
        api_result = {
            'MovieName': 'Dragons.defenders.of.berk',
            'MovieKind': 'movie'
        }

        serie1 = 'Dragons.defenders.of.berk.S05e10.fap'
        self.assertFalse(compare(serie1, api_result))

        api_result['MovieKind'] = 'web series'
        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '9'
        self.assertFalse(compare(serie1, api_result))

        api_result['SeriesSeason'] = '4'
        api_result['SeriesEpisode'] = '10'
        self.assertFalse(compare(serie1, api_result))

        api_result['SeriesSeason'] = '5'
        api_result['SeriesEpisode'] = '10'
        self.assertTrue(compare(serie1, api_result))

        serie1 = 'Dragons.riders.of.berk.S05e10.fap'
        self.assertTrue(compare(serie1, api_result))

        api_result['MovieName'] = 'Dragons.riders.of.berk'
        api_result['MovieKind'] = 'movie'
        api_result['MovieYear'] = '2014'
        movie1 = 'Dragons.defenders.of.berk (2014)'
        self.assertTrue(compare(movie1, api_result))

        api_result['MovieYear'] = '2013'
        self.assertFalse(compare(movie1, api_result))

        movie1 = 'Dragons.defenders.of.berk'
        self.assertTrue(compare(movie1, api_result))

    def test_letter_coverage(self):
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

    def test_change_token_to_dot(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/....?'
        self.assertEqual('The.Walking.Dead.', change_token_to_dot(serie_name1))

    def test_rename_serie(self):
        serie_name1 = 'The;;#!"$%^&*()_Walking<>?:@~{}Dead\\\\/..25x15..?'
        self.assertEqual('The.Walking.Dead.S25E15.', rename_serie(serie_name1))

    def test_get_episode(self):
        tmp_dir = tempfile.mkdtemp()
        f1 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E04.mkv')
        f2 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E02.mkv')
        f3 = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix='S01E05.mkv')

        self.assertIsNone(get_episode(tmp_dir, 'useless arg', '01'))
        self.assertIsNotNone(get_episode(tmp_dir, 'useless arg', '02'))
        self.assertIsNone(get_episode(tmp_dir, 'useless arg', '03'))

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