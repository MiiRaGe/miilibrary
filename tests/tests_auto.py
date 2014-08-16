__author__ = 'MiiRaGe'

import logging
import os
import unittest

import settings
import tools


class TestUnpackerMain(unittest.TestCase):
    def setUp(self):
        settings.SOURCE_FOLDER = os.path.abspath('./tests/test_input/')
        settings.DESTINATION_FOLDER = os.path.abspath('./tests/test_output/')
        abs_data = os.path.abspath('./tests/test_data/')
        for media_file in os.listdir(abs_data):
            os.link(os.path.join(abs_data, media_file), os.path.join(abs_data, media_file))

        tools.remove_handler()
        abs_log_file = os.path.abspath('./tests/test_log')
        try:
            os.remove(abs_log_file)
        except OSError:
            pass
        test_handler = logging.FileHandler(abs_log_file)
        logging.getLogger('NAS').addHandler(test_handler)

    def tearDown(self):
        abs_input = os.path.abspath('./tests/test_input/')
        for media_file in os.listdir(abs_input):
            if media_file == '.gitignore':
                continue
            tools.delete_file(os.path.join(abs_input, media_file))
        abs_output = os.path.abspath('./tests/test_output/')
        for media_file in os.listdir(abs_output):
            if media_file == '.gitignore':
                continue
            tools.delete_dir(os.path.join(abs_output, media_file))

    def test_hello_world(self):
        self.assertEqual(True, True)
        print 'Hello'