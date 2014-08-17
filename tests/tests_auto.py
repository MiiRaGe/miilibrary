__author__ = 'MiiRaGe'

import logging
import os
import shutil
import unittest

import settings
import miinaslibrary
import tools

from sorter.Sorter import is_serie, apply_custom_renaming, format_serie_name, change_token_to_dot, \
    compare, letter_coverage

tools.remove_handler()
abs_log_file = '%s/test_log.LOG' % os.path.dirname(__file__)
try:
    os.remove(abs_log_file)
except OSError:
    pass
test_handler = logging.FileHandler(abs_log_file)
logging.getLogger('NAS').addHandler(test_handler)


class TestMain(unittest.TestCase):
    def setUp(self):
        print("*** Building environment ***")
        settings.SOURCE_FOLDER = '%s/test_input/' % os.path.dirname(__file__)
        settings.DESTINATION_FOLDER = '%s/test_output/' % os.path.dirname(__file__)

        abs_data = '%s/test_data/'  % os.path.dirname(__file__)
        print "\t ** Moving Files **"
        try:
            for media_file in os.listdir(abs_data):
                print "\t\t * Moving: %s*" % media_file
                shutil.copy(os.path.join(abs_data, media_file), os.path.join(settings.SOURCE_FOLDER, media_file))
        except WindowsError:
            print "\t\t * No data to move... tests are void **"
        print("*** Environment Builded ***")

    def tearDown(self):
        print("*** Tearing down environment ***")
        abs_input = os.path.abspath('./tests/test_input/')
        print "\t ** Cleaning input Files **"
        try:
            for media_file in os.listdir(abs_input):
                if media_file == '.gitignore':
                    continue
                print "\t\t * Removing: %s *" % media_file
                tools.delete_file(os.path.join(abs_input, media_file))
        except WindowsError:
            print "\t\t * No data to move... tests are void **"

        print "\t ** Cleaning output directory **"
        abs_output = os.path.abspath('./tests/test_output/')
        try:
            for media_file in os.listdir(abs_output):
                if media_file == '.gitignore':
                    continue
                print "\t\t * Removing: %s *" % media_file
                tools.delete_dir(os.path.join(abs_output, media_file))
        except WindowsError:
            print "\t\t * No data to move... tests are void **"

        print("*** Environment Torn Down***")

    def test_main(self):
        print "== Testing validate_settings =="
        self.assertTrue(tools.validate_settings())

        print "== Testing doUnpack =="
        miinaslibrary.doUnpack(settings.SOURCE_FOLDER)


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