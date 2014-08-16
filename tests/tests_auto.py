__author__ = 'MiiRaGe'

import logging
import os
import shutil
import unittest

import settings
import tools


class TestMain(unittest.TestCase):
    def setUp(self):
        print("*** Building environment ***")
        settings.SOURCE_FOLDER = os.path.abspath('./tests/test_input/')
        settings.DESTINATION_FOLDER = os.path.abspath('./tests/test_output/')

        abs_data = os.path.abspath('./tests/test_data/')
        print "\t ** Moving Files **"
        try:
            for media_file in os.listdir(abs_data):
                print "\t\t * Moving: %s*" % media_file
                shutil.copy(os.path.join(abs_data, media_file), os.path.join(settings.SOURCE_FOLDER, media_file))
        except WindowsError:
            print "\t\t * No data to move... tests are void **"

        print "\t ** Changing log file **"
        tools.remove_handler()
        abs_log_file = os.path.abspath('./tests/test_log.LOG')
        try:
            os.remove(abs_log_file)
        except OSError:
            pass
        test_handler = logging.FileHandler(abs_log_file)
        logging.getLogger('NAS').addHandler(test_handler)
        print("*** Environment Builded ***")

    def tearDown(self):
        print("*** Tearing down environment ***")
        abs_input = os.path.abspath('./tests/test_input/')
        print "\t ** Cleaning input Files **"
        for media_file in os.listdir(abs_input):
            if media_file == '.gitignore':
                continue
            print "\t\t * Removing: %s *" % media_file
            tools.delete_file(os.path.join(abs_input, media_file))

        print "\t ** Cleaning output directory **"
        abs_output = os.path.abspath('./tests/test_output/')
        for media_file in os.listdir(abs_output):
            if media_file == '.gitignore':
                continue
            print "\t\t * Removing: %s *" % media_file
            tools.delete_dir(os.path.join(abs_output, media_file))
        print("*** Environment Torn Down***")

    def test_main(self):
        print "== Testing validate_settings =="
        self.assertTrue(tools.validate_settings())

        import miinaslibrary
        print "== Testing doUnpack =="
        miinaslibrary.doUnpack(settings.SOURCE_FOLDER)