import json
import mock
import os

from django.conf import settings
from django.test import override_settings

from apply_index_local import apply_index
from mii_common import tools
from utils.base import TestMiilibrary


@override_settings(DUMP_INDEX_JSON_FILE_NAME='lol.json')
class TestApplyIndex(TestMiilibrary):
    def setUp(self):
        super().setUp()

    def _dump_index(self, dict_index):
        index_path = os.path.join(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        self.fs.create_file(index_path,
                           contents=json.dumps(dict_index))
        return index_path

    @mock.patch('apply_index_local.json.loads')
    def test_return_immediately(self, loads):
        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        assert not loads.called

    def test_apply_index(self):
        fake_index = {
            'Actor': {
                'Michal':
                    [
                        ('Thor.(2011)', self.SOURCE_FOLDER),
                        ('Thor.2.(2016)', self.SOURCE_FOLDER),
                    ]
            }
        }
        index_path = self._dump_index(fake_index)

        movies = tools.make_dir(os.path.join(self.DESTINATION_FOLDER, 'Movies'))
        tools.make_dir(os.path.join(movies, 'Index'))
        assert os.path.exists(index_path)
        apply_index(self.DESTINATION_FOLDER, 'lol.json')
        assert not os.path.exists(index_path)
        root = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index')
        assert os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.(2011)'))
        assert os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.2.(2016)'))

    def test_apply_index_diff(self):
        fake_index = {
            'Actor': {
                'Michal':
                    [
                        ('Thor.(2011)', self.SOURCE_FOLDER),
                        ('Thor.2.(2016)', self.SOURCE_FOLDER),
                    ]
            }
        }
        self._dump_index(fake_index)

        movies = tools.make_dir(os.path.join(self.DESTINATION_FOLDER, 'Movies'))
        tools.make_dir(os.path.join(movies, 'Index'))

        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        root = os.path.join(self.DESTINATION_FOLDER, 'Movies', 'Index')

        assert os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.(2011)'))
        assert os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.2.(2016)'))

        fake_index = {
            'Actor': {
                'Michal':
                    [
                        ('Thor.3.(2011)', self.SOURCE_FOLDER),
                    ]
            }
        }
        self._dump_index(fake_index)
        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        assert os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.3.(2011)'))
        assert not os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.(2011)'))
        assert not os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.2.(2016)'))

        fake_index = {
            'Actor': {
                'Michol':
                    [
                        ('Thor.3.(2011)', self.SOURCE_FOLDER),
                    ]
            }
        }
        self._dump_index(fake_index)
        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        assert not os.path.exists(os.path.join(root, 'Actor', 'Michal', 'Thor.3.(2011)'))
        assert os.path.exists(os.path.join(root, 'Actor', 'Michol', 'Thor.3.(2011)'))

        fake_index = {
            'Genre': {
                'Drama':
                    [
                        ('Thor.3.(2011)', self.SOURCE_FOLDER),
                    ]
            }
        }
        self._dump_index(fake_index)
        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        assert not os.path.exists(os.path.join(root, 'Actor', 'Michol', 'Thor.3.(2011)'))
        assert os.path.exists(os.path.join(root, 'Genre', 'Drama', 'Thor.3.(2011)'))
