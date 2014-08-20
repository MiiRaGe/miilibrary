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

from sorter.Sorter import is_serie, apply_custom_renaming, format_serie_name, change_token_to_dot, \
    compare, letter_coverage, rename_serie, get_episode, get_quality, get_info

abs_log_file = '%s/test_log.LOG' % os.path.dirname(__file__)
try:
    os.remove(abs_log_file)
except OSError:
    pass
test_handler = logging.FileHandler(abs_log_file)
logger = logging.getLogger('NAS')
logger.addHandler(test_handler)

try:
    raise WindowsError
except NameError:
    WindowsError = None
else:
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
            for media_file in os.listdir(abs_input):
                if media_file == '.gitignore':
                    continue
                logger.info("\t\t * Removing: %s *" % media_file)
                tools.delete_file(os.path.join(abs_input, media_file))
        except WindowsError:
            logger.info("\t\t * No data to move... tests are void **")

        logger.info("\t ** Cleaning output directory **")
        abs_output = self.DESTINATION_FOLDER
        try:
            for media_file in os.listdir(abs_output):
                if media_file == '.gitignore':
                    continue
                logger.info("\t\t * Removing: %s *" % media_file)
                shutil.rmtree(os.path.join(abs_output, media_file))
        except WindowsError:
            logger.info("\t\t * No data to move... tests are void **")

        logger.info("*** Environment Torn Down***")

    def test_main(self):
        with patch.multiple(settings, SOURCE_FOLDER=self.SOURCE_FOLDER, DESTINATION_FOLDER=self.DESTINATION_FOLDER):
            logger.info("== Testing validate_settings ==")
            self.assertTrue(tools.validate_settings())

            logger.info("== Testing doUnpack ==")
            mnl = MiiNASLibrary()
            mnl.doUnpack()
            self.assertEqual(len(os.listdir(self.DESTINATION_FOLDER + '/data')), 4)


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
        name = 'The.Matrix.2001'
        res = get_info(name)
        self.assertEqual(res['title'], 'The Matrix')
        self.assertEqual(res['year'], '2001')

        name = 'Hancock.(2004)'
        res = get_info(name)
        self.assertEqual(res['title'], 'Hancock')
        self.assertEqual(res['year'], '2004')

        name = '2012.(2007)'
        res = get_info(name)
        self.assertEqual(res['title'], '2012')
        self.assertEqual(res['year'], '2007')

        name = '2012.720p'
        res = get_info(name)
        self.assertEqual(res['title'], '2012')
        self.assertIsNone(res.get('year'))

        name = 'Iron Man 3'
        res = get_info(name)
        self.assertEqual(res['title'], name)