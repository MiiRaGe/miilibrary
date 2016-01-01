# -*- coding: utf-8 -*-

import logging
from subprocess import CalledProcessError

import mock
import os

from datetime import timedelta
from django.test import override_settings
from django.utils import timezone

from mii_common import tools
from mii_indexer.models import MovieRelation
from mii_indexer.models import MovieTagging, Person
from mii_sorter.models import Movie, Episode, Serie, Season, get_serie_episode, WhatsNew
from mii_unpacker.factories import UnpackedFactory
from mii_unpacker.logic import RecursiveUnrarer
from utils.base import TestMiilibrary

logger = logging.getLogger(__name__)


@mock.patch('mii_unpacker.logic.link', new=mock.MagicMock(side_effect=AttributeError))
class TestMain(TestMiilibrary):
    def test_unpack(self):
        logger.info("== Testing doUnpack ==")
        self.recursive_unrarer.run()
        assert len(os.listdir(self.DESTINATION_FOLDER + '/data')) == 5

    def test_sort(self):
        self._fill_data()
        self.sorter.sort()
        assert Movie.objects.all().count() == 2
        assert Episode.objects.all().count() == 1
        assert WhatsNew.objects.all().count() == 3

    def test_sort_movie(self):
        self._fill_data()
        self.sorter.sort()
        assert Movie.objects.get(title='Thor', year=2011)
        assert Movie.objects.get(title='Thor- The Dark World', year=2013)

        assert len(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All'))) == 2
        assert 'Thor- The Dark World (2013)' in os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today'))
        assert 'Thor (2011)' in os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today'))

    def test_sort_serie(self):
        self._fill_data()
        self.sorter.sort()
        assert get_serie_episode('The Big Bank Theory', 1, 1)
        assert 'The.Big.Bank.Theory.S01E01.[720p].mkv' in os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New', 'Today'))
        tbbt_s1 = os.path.join(self.DESTINATION_FOLDER, 'TVSeries', 'The Big Bank Theory', 'Season 1')
        assert len(os.listdir(tbbt_s1)) == 1

    def test_new(self):
        today = timezone.now()
        for i in range(0, 70):
            WhatsNew.objects.create(path=self.DESTINATION_FOLDER, date=today - timedelta(days=i), name=i)
        self.sorter.update_new()
        expected = ['1 month(s) ago', '1 week(s) ago', '2 day(s) ago', '2 week(s) ago', '3 day(s) ago', '3 week(s) ago',
                    '4 day(s) ago', '4 week(s) ago', '5 day(s) ago', '6 day(s) ago', 'Today', 'Yesterday']
        assert sorted(os.listdir(os.path.join(self.DESTINATION_FOLDER, 'New'))) == sorted(expected)

    def test_index(self):
        self._fill_movie()
        movie1 = Movie.objects.create(title='Thor', year='2011', imdb_id='0800369', file_size=10)
        movie1.file_path = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor (2011)', 'Thor.(2011).720p.mkv')
        movie1.save()
        movie2 = Movie.objects.create(title='Thor- The Dark World', year='2013', imdb_id='1981115', file_size=10)
        movie2.file_path = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor- The Dark World (2013)', 'Thor-.The.Dark.World.(2013).720p.mkv')
        movie2.save()
        self.indexer.index()
        index_root_folder = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index')
        index_year_folder = os.path.join(index_root_folder, 'Years')
        index_genre_folder = os.path.join(index_root_folder, 'Genres')
        index_directors_folder = os.path.join(index_root_folder, 'Directors')
        index_ratings_folder = os.path.join(index_root_folder, 'Ratings')
        index_actor_folder = os.path.join(index_root_folder,'Actors')

        assert os.listdir(index_year_folder) == ['2011', '2013']
        assert os.listdir(index_genre_folder) == ['Action', 'Adventure', 'Bullshit', 'Fantasy', 'London', 'Romance']
        assert os.listdir(index_directors_folder) == ['Alan Taylor', 'Joss Whedon', 'Kenneth Branagh']

        assert 'Chris Hemsworth' in os.listdir(index_actor_folder)
        assert 'Natalie Portman' in os.listdir(index_actor_folder)
        assert 'Tom Hiddleston' in os.listdir(index_actor_folder)
        assert os.listdir(index_ratings_folder) == ['7.0', '9.5']
        assert os.listdir(os.path.join(index_ratings_folder, '7.0')) == ['Thor (2011)']

    def test_unpack_sort_index(self):
        self.recursive_unrarer.run()
        assert len(os.listdir(self.DESTINATION_FOLDER + '/data')) == 5

        self.sorter.sort()

        assert Movie.objects.all().count() == 2

        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')) == 2
        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')) == 1
        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')) == 1

        assert Episode.objects.get(number=1)
        assert Season.objects.get(number=1)
        assert Serie.objects.get(name='The Big Bank Theory')

        assert 'The Big Bank Theory' in os.listdir(self.DESTINATION_FOLDER + '/TVSeries')
        assert 'Season 1' in os.listdir(self.DESTINATION_FOLDER + '/TVSeries/The Big Bank Theory')

        tbbt_season1_folder = os.path.join(self.DESTINATION_FOLDER, 'TVSeries', 'The Big Bank Theory', 'Season 1')
        assert 'The.Big.Bank.Theory.S01E01.[720p].mkv' in os.listdir(tbbt_season1_folder)

        assert MovieTagging.objects.count() == 0
        assert MovieRelation.objects.count() == 0
        assert Person.objects.count() == 0
        self.indexer.index()
        assert MovieTagging.objects.count() == 7
        assert MovieRelation.objects.count() == 33
        assert Person.objects.count() == 22

    @override_settings(DUMP_INDEX_JSON_FILE_NAME='data.json')
    def test_json_dump(self):
        self.recursive_unrarer.run()
        assert len(os.listdir(self.DESTINATION_FOLDER + '/data')) == 5

        self.sorter.sort()

        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All')) == 2
        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor (2011) [720p]')) == 1
        assert len(os.listdir(self.DESTINATION_FOLDER + '/Movies/All/Thor- The Dark World (2013)')) == 1

        tv_series_folder = os.path.join(self.DESTINATION_FOLDER, 'TVSeries')
        assert 'The Big Bank Theory' in os.listdir(tv_series_folder)

        tbbt_folder = os.path.join(tv_series_folder, 'The Big Bank Theory')
        assert 'Season 1' in os.listdir(tbbt_folder)

        tbbt_season1_folder = os.path.join(tbbt_folder, 'Season 1')
        assert 'The.Big.Bank.Theory.S01E01.[720p].mkv' in os.listdir(tbbt_season1_folder)

        self.indexer.index()
        assert os.path.exists(self.DESTINATION_FOLDER + '/data.json')

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


class TestSpecificUnpacker(TestMiilibrary):
    def setUp(self):
        self.setUpPyfakefs()
        self.SOURCE_FOLDER = '/raw/'
        self.DESTINATION_FOLDER = '/processed/'
        tools.make_dir(self.DESTINATION_FOLDER)
        tools.make_dir(self.SOURCE_FOLDER)
        self.recursive_unrarer = RecursiveUnrarer()

    @mock.patch('mii_unpacker.logic.unrar')
    def test_already_unrared(self, unrar):
        UnpackedFactory.create(filename='Thor.2.rar')
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.rar', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert not unrar.called
        assert self.recursive_unrarer.extracted == 0

    @mock.patch('mii_unpacker.logic.unrar')
    def test_unrar(self, unrar):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.rar', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert unrar.called
        assert self.recursive_unrarer.extracted == 1

    @mock.patch('mii_unpacker.logic.unrar')
    def test_unrar_raising_error(self, unrar):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.rar', contents=self._generate_data(1))
        unrar.side_effect = CalledProcessError('', '', '')
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.extracted == 0

    def test_linking_video(self):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.mkv', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.linked == 1

    def test_linking_video_already_exists(self):
        UnpackedFactory.create(filename='Thor.2.mkv')
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.mkv', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.linked == 0

    def test_linking_video_file_exists_but_less(self):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.mkv', contents=self._generate_data(1))
        self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2.mkv', contents=self._generate_data(2))
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.linked == 0

    def test_linking_video_file_exists_betters(self):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.mkv', contents=self._generate_data(2))
        self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2.mkv', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.linked == 1

    @mock.patch('mii_unpacker.logic.link', new=mock.MagicMock(side_effect=AttributeError))
    def test_linking_video_file_exists_betters_link_fails(self):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'Thor.2.mkv', contents=self._generate_data(2))
        self.fs.CreateFile(self.DESTINATION_FOLDER + '/data/Thor.2.mkv', contents=self._generate_data(1))
        self.recursive_unrarer.unrar_and_link()
        assert self.recursive_unrarer.linked == 1





