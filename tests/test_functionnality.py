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
from mii_sorter.factories import MovieFactory, EpisodeFactory
from mii_sorter.logic import Sorter, get_dir_size, get_size
from mii_sorter.models import Movie, Episode, Serie, Season, get_serie_episode, WhatsNew
from mii_unpacker.factories import UnpackedFactory
from mii_unpacker.logic import RecursiveUnrarer
from utils.base import TestMiilibrary, mii_osdb_mock

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
        assert 'The.Big.Bank.Theory.S01E01.[720p].mkv' in os.listdir(
            os.path.join(self.DESTINATION_FOLDER, 'New', 'Today'))
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
        movie2.file_path = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'All', 'Thor- The Dark World (2013)',
                                        'Thor-.The.Dark.World.(2013).720p.mkv')
        movie2.save()
        self.indexer.index()
        index_root_folder = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index')
        index_year_folder = os.path.join(index_root_folder, 'Years')
        index_genre_folder = os.path.join(index_root_folder, 'Genres')
        index_directors_folder = os.path.join(index_root_folder, 'Directors')
        index_ratings_folder = os.path.join(index_root_folder, 'Ratings')
        index_actor_folder = os.path.join(index_root_folder, 'Actors')

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

    @mock.patch('mii_unpacker.logic.unrar')
    def test_unicode_archive(self, unrar):
        self.fs.CreateFile(self.SOURCE_FOLDER + u'ééü.rar', contents=self._generate_data(2))
        self.recursive_unrarer.unrar_and_link()

    @mock.patch('mii_unpacker.logic.unrar')
    def test_unicode_archive(self, unrar):
        self.fs.CreateFile(self.SOURCE_FOLDER + 'ééü.mkv', contents=self._generate_data(2))
        self.recursive_unrarer.unrar_and_link()


class TestSpecificSorter(TestMiilibrary):
    def setUp(self):
        self.setUpPyfakefs()
        self.DESTINATION_FOLDER = '/processed/'
        tools.make_dir(self.DESTINATION_FOLDER)
        tools.make_dir(os.path.join(self.DESTINATION_FOLDER, 'data'))
        self.sorter = Sorter()
        self.sorter.mii_osdb = mii_osdb_mock
        self.data_path = os.path.join(self.DESTINATION_FOLDER, 'data')

    def test_get_size(self):
        f1 = os.path.join(self.data_path, 'file1')
        f2 = os.path.join(self.data_path, 'file2')
        self.fs.CreateFile(f1, contents=self._generate_data(1))
        self.fs.CreateFile(f2, contents=self._generate_data(1))
        dir_size = get_dir_size(self.data_path)
        assert dir_size >= (get_size(f1) + get_size(f2))

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_is_called(self):
        self.fs.CreateFile(os.path.join(self.data_path, 'test_file.mkv'), contents='test_file' * 65535)
        self.sorter.sort_open_subtitle_info = mock.MagicMock()
        self.sorter.sort()
        assert self.sorter.sort_open_subtitle_info.called

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_is_called_with_get_movie_name(self):
        self.fs.CreateFile(os.path.join(self.data_path, 'test_file.mkv'), contents='test_file' * 65535)
        self.sorter.sort_open_subtitle_info = mock.MagicMock()
        self.sorter.mii_osdb.get_subtitles = mock.MagicMock(return_value=False)
        self.sorter.sort()
        assert self.sorter.sort_open_subtitle_info.called

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_is_called_with_error(self):
        self.fs.CreateFile(os.path.join(self.data_path, 'test_file.mkv'), contents='test_file' * 65535)
        self.sorter.sort_open_subtitle_info = mock.MagicMock(side_effect=Exception('test'))
        self.sorter.sort()
        assert self.sorter.sort_open_subtitle_info.called

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_info_movie(self):
        os_info = {
            'MovieHash': '123',
            'MovieKind': 'movie',
            'MovieName': 'name',
            'MovieYear': 'year',
            'IDMovieImdb': 'id',
        }
        self.sorter.map = {'123': 'test_file.mkv'}
        self.sorter.create_dir_and_move_movie = mock.MagicMock()
        self.sorter.sort_open_subtitle_info(os_info)
        self.sorter.create_dir_and_move_movie.assert_called_with('name', 'year', 'id', 'test_file.mkv')

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_info_movie_with_name(self):
        os_info = {
            'MovieHash': '123',
            'MovieKind': 'serie',
            'MovieName': '"Arrow" My Name is oliver queer',
            'SeriesSeason': '1',
            'SeriesEpisode': '1',
        }
        self.sorter.map = {'123': 'test_file.mkv'}
        self.sorter.create_dir_and_move_serie = mock.MagicMock()
        self.sorter.sort_open_subtitle_info(os_info)
        self.sorter.create_dir_and_move_serie.assert_called_with('Arrow', '1', '1', 'My Name is oliver queer',
                                                                 'test_file.mkv')

    @mock.patch('mii_sorter.logic.get_best_match', new=lambda x, y: x[0])
    def test_sort_open_subtitle_info_movie_without_name_0_exception(self):
        os_info = {
            'MovieHash': '123',
            'MovieKind': 'serie',
            'MovieName': 'Arrow',
            'SeriesSeason': '0',
            'SeriesEpisode': '1',
            'SubFileName': 'ArrowS01E01.mkv',
        }
        self.sorter.map = {'123': 'test_file.mkv'}
        self.sorter.create_dir_and_move_serie = mock.MagicMock()
        self.sorter.sort_open_subtitle_info(os_info)
        self.sorter.create_dir_and_move_serie.assert_called_with('Arrow', '1', '01', '',
                                                                 'test_file.mkv')

    def test_create_dir_and_move_movie_to_unsorted(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        MovieFactory.create(file_size=5000, title='test', folder_path=existing_file, year=1500)
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        self.sorter.move_to_unsorted = mock.MagicMock()
        assert not self.sorter.create_dir_and_move_movie('test', 1500, '1', 'test.mkv')
        self.sorter.move_to_unsorted.assert_called_with(test_file)

    @mock.patch('mii_sorter.logic.tools.delete_dir')
    def test_create_dir_and_move_movie_same_size(self, delete_dir):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        MovieFactory.create(file_size=os.path.getsize(test_file), title='test', folder_path=existing_file, year=1500)
        assert not self.sorter.create_dir_and_move_movie('test', 1500, '1', 'test.mkv')
        delete_dir.assert_called_with(test_file)

    @mock.patch('mii_sorter.logic.tools.delete_dir')
    def test_create_dir_and_move_movie_error_handling(self, delete_dir):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        MovieFactory.create(file_size=os.path.getsize(test_file), title='test', folder_path=existing_file, year=1500)
        delete_dir.side_effect = OSError()
        assert not self.sorter.create_dir_and_move_movie('test', 1500, '1', 'test.mkv')
        delete_dir.side_effect = Exception()
        assert not self.sorter.create_dir_and_move_movie('test', 1500, '1', 'test.mkv')

    def test_create_dir_and_move_serie_to_unsorted(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        EpisodeFactory.create(file_size=5000, season__serie__name='Test', file_path=existing_file, season__number=1,
                              number=1)
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        self.sorter.move_to_unsorted = mock.MagicMock()
        assert not self.sorter.create_dir_and_move_serie('test', '1', '1', 'title', 'test.mkv')
        self.sorter.move_to_unsorted.assert_called_with(test_file)

    def test_create_dir_and_move_serie_error_handling(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        EpisodeFactory.create(file_size=5000, season__serie__name='Test', file_path=existing_file, season__number=1,
                              number=1)
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        self.sorter.move_to_unsorted = mock.MagicMock()
        self.sorter.move_to_unsorted.side_effect = OSError()
        assert not self.sorter.create_dir_and_move_serie('test', '1', '1', 'title', 'test.mkv')

    def test_create_dir_and_move_serie_same_size(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        EpisodeFactory.create(file_size=os.path.getsize(test_file), season__serie__name='Test', file_path=existing_file,
                              season__number=1, number=1)
        assert not self.sorter.create_dir_and_move_serie('test', '1', '1', 'title', 'test.mkv')

    def test_create_dir_and_move_serie_new_is_bigger(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        self.sorter.move_to_unsorted = mock.MagicMock()
        EpisodeFactory.create(file_size=os.path.getsize(test_file) - 1, season__serie__name='Test',
                              file_path=existing_file, season__number=1, number=1)
        assert self.sorter.create_dir_and_move_serie('test', '1', '1', 'title', 'test.mkv')
        self.sorter.move_to_unsorted.assert_called_with(existing_file)

    def test_create_dir_and_move_serie_replace_missing(self):
        existing_file = os.path.join(self.data_path, 'test2.mkv')
        test_file = os.path.join(self.data_path, 'test.mkv')
        self.fs.CreateFile(test_file, contents='test_file')
        self.fs.CreateFile(existing_file, contents='test_file')
        EpisodeFactory.create(file_size=os.path.getsize(test_file), season__serie__name='Test',
                              file_path='/unknown_path', season__number=1, number=1)
        assert self.sorter.create_dir_and_move_serie('test', '1', '1', 'title', 'test.mkv')

    @mock.patch('mii_sorter.logic.get_info')
    def test_sort_movie_from_name(self, get_info):
        get_info.return_value = None
        assert not self.sorter.sort_movie_from_name('')

    def test_sort_movie_from_name_no_match(self):
        self.sorter.mii_tmdb = mock.MagicMock()
        self.sorter.mii_tmdb.get_movie_name.return_value = {
            'results':
                [
                    {'id': '12345',
                     'release_date': '1900-01-01'}
                ]
        }
        self.sorter.mii_tmdb.get_movie_imdb_id.return_value = 'asdf'
        assert not self.sorter.sort_movie_from_name('Movie.(2000).mkv')

    def test_sort_movie_from_name_no_match_title(self):
        self.sorter.mii_tmdb = mock.MagicMock()
        self.sorter.mii_tmdb.get_movie_name.return_value = {
            'results':
                [
                    {'id': '12345',
                     'release_date': '2000-01-01',
                     'title': 'asdfs'}
                ]
        }
        assert not self.sorter.sort_movie_from_name('Movie.(2000).mkv')

    def test_move_to_unsorted(self):
        self.fs.CreateFile('/test.mkv', contents='a')
        self.fs.CreateFile('/unsorted/test.mkv', contents='b')
        self.sorter.unsorted_dir = '/unsorted'
        self.sorter.move_to_unsorted('/', 'test.mkv')
        assert not os.path.exists('/test.mkv')
        assert os.path.exists('/unsorted/test.mkv')
