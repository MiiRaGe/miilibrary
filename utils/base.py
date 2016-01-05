import mock
import os
import random
import string


from django.test import override_settings, TestCase as DjTestCase
from fake_filesystem_unittest import Patcher, TestCase

from mii_common import tools
from mii_indexer.logic import Indexer
from mii_sorter.logic import Sorter
from mii_unpacker.logic import RecursiveUnrarer
from mock_osdb import *
from mock_tmdb import *

mii_osdb_mock = mock.MagicMock()
mii_osdb_mock.get_movie_name = mock_get_movie_names2
mii_osdb_mock.get_imdb_information = mock_get_imdb_information
mii_osdb_mock.get_movie_names = mock_get_movie_names
mii_osdb_mock.get_subtitles = mock_get_subtitles

mii_tmdb_mock = mock.MagicMock()
mii_tmdb_mock.get_movie_name = mock_get_movie_name
mii_tmdb_mock.get_movie_imdb_id = mock_get_movie_imdb_id

Patcher.SKIPNAMES.add('py')
Patcher.SKIPNAMES.add('pytest')
Patcher.SKIPNAMES.add('_pytest')


@override_settings(MINIMUM_SIZE=0, NAS_IP=None, NAS_USERNAME=None,
                   SOURCE_FOLDER='/raw/',
                   DESTINATION_FOLDER='/processed/',
                   DUMP_INDEX_JSON_FILE_NAME=None,
                   REPORT_ENABLED=False)
class TestMiilibrary(TestCase, DjTestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.SOURCE_FOLDER = '/raw/'
        self.DESTINATION_FOLDER = '/processed/'
        tools.make_dir(self.DESTINATION_FOLDER)
        tools.make_dir(self.SOURCE_FOLDER)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'The.big.bank.theory.S01E01.720p.mkv', contents='TheBigBank' * 65535)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'The.big.bank.theory.S01E01.mkv', contents='TheBig' * 65535)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.(2011).720p.mkv', contents='Thor' * 65535)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.(2011).mkv', contents='Tho' * 65535)
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor-sample.mkv', contents=self._generate_data(1))
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.rar', contents=self._generate_data(1))
        self.fs.CreateFile(self.SOURCE_FOLDER + '/sub/Thor.2.part01.rar', contents=self._generate_data(1))
        self.fs.CreateFile(self.SOURCE_FOLDER + '/sub/Thor.2.part02.rar', contents=self._generate_data(1))

        def fake_unrar(*args, **kwargs):
            try:
                self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2-sample.mkv', contents=self._generate_data(1))
                self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2.srt', contents=self._generate_data(1))
                self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.The.Dark.World.mkv',
                                   contents='Thor2' * 65535)
            except IOError:
                pass
        self.recursive_unrarer = RecursiveUnrarer()
        self.recursive_unrarer.unrar = fake_unrar
        self.recursive_unrarer.unrar = fake_unrar
        self.sorter = Sorter()
        self.sorter.mii_osdb = mii_osdb_mock
        self.sorter.mii_tmdb = mii_tmdb_mock
        self.indexer = Indexer()
        self.indexer.mii_osdb = mii_osdb_mock

    def _generate_data(self, size):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10000 * size))

    def _fill_data(self):
        def lazy_creation(filename, contents=None):
            self.fs.CreateFile(os.path.join(self.DESTINATION_FOLDER, 'data', filename), contents=contents)
        lazy_creation('The.big.bank.theory.S01E01.720p.mkv', contents='TheBigBank' * 65535)
        lazy_creation('The.big.bank.theory.S01E01.mkv', contents='TheBig' * 65535)
        lazy_creation('Thor.(2011).720p.mkv', contents='Thor' * 65535)
        lazy_creation('Thor.(2011).mkv', contents='Tho' * 65535)
        lazy_creation('Thor.The.Dark.World.mkv', contents='Tho' * 65535)

    def _fill_movie(self):
        os.mkdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor (2011)'))
        os.mkdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor- The Dark World (2013)'))

        self.fs.CreateFile(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor (2011)', 'Thor.(2011).720p.mkv'),
                           contents='Thor' * 65535)
        self.fs.CreateFile(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor- The Dark World (2013)', 'Thor-.The.Dark.World.(2013).720p.mkv'),
                           contents='Tho' * 65535)
