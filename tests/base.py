import mock
import os

from django.test import override_settings, TestCase as DjTestCase
from fake_filesystem_unittest import Patcher, TestCase

from miinaslibrary import MiiNASLibrary
from mock_osdb import *
from mock_tmdb import *

mii_osdb_mock = mock.MagicMock()
mii_osdb_mock.get_movie_name = mock_get_movie_names2
mii_osdb_mock.get_imdb_information = mock_get_imdb_information
mii_osdb_mock.get_movie_names = mock_get_movie_names
mii_osdb_mock.get_subtitles = mock_get_movie_names

mii_tmdb_mock = mock.MagicMock()
mii_tmdb_mock.get_movie_name = mock_get_movie_name
mii_tmdb_mock.get_movie_imdb_id = mock_get_movie_imdb_id

#
# Patcher.SKIPNAMES.add('py')
# Patcher.SKIPNAMES.add('pytest')
# Patcher.SKIPNAMES.add('_pytest')

@override_settings(MINIMUM_SIZE=0, NAS_IP=None, NAS_USERNAME=None,
                   SOURCE_FOLDER='/raw/',
                   DESTINATION_FOLDER='/processed/')
@mock.patch('mii_indexer.indexer.Indexer.mii_osdb', new=mii_osdb_mock)
@mock.patch('mii_unpacker.unpacker.Unpacker.unrar')
class TestMiilibrary(TestCase, DjTestCase):

    def setUp(self):
        self.setUpPyfakefs()
        self.SOURCE_FOLDER = '/raw/'
        self.DESTINATION_FOLDER = '/processed/'
        os.mkdir(self.DESTINATION_FOLDER)
        os.mkdir(self.SOURCE_FOLDER)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'The.big.bank.theory.S01E01.720p.mkv', contents=self._generate_data(2))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'The.big.bank.theory.S01E01.mkv', contents=self._generate_data(1))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.(2011).720p.mkv', contents=self._generate_data(4))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.(2011).mkv', contents=self._generate_data(3))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor-sample.mkv', contents=self._generate_data(1))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.rar', contents=self._generate_data(1))

        def fake_unrar(*args, **kwargs):
            self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2-sample.mkv', contents=self._generate_data(1))
            self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.The.Dark.World.mkv', contents=self._generate_data(6))
        self.mnl = MiiNASLibrary()
        self.mnl.recursive_unrarer.unrar = fake_unrar
        self.mnl.sorter.mii_osdb = mii_osdb_mock
        self.mnl.sorter.mii_tmdb = mii_tmdb_mock
        self.mnl.indexer.mii_osdb = mii_osdb_mock

    def _generate_data(self, size):
        content = ''
        for i in range(0, size):
            content += 'a' * 100
        return content
