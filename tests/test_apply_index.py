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
    @mock.patch('apply_index_local.json.loads')
    def test_return_immediately(self, loads):
        apply_index(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        assert not loads.called

    @mock.patch('apply_index_local.tools.dict_apply')
    def test_apply_index(self, dict_apply):
        fake_index = {
            'Actor': {
                'Michael Douglas':
                    [
                        ('Thor.(2011).mkv', self.SOURCE_FOLDER + 'Thor.(2011).mkv'),
                        ('Thor.(2011).720p.mkv', self.SOURCE_FOLDER + 'Thor.(2011).720p.mkv'),
                    ]
            }
        }
        index_path = os.path.join(self.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
        self.fs.CreateFile(index_path,
                           contents=json.dumps(fake_index))
        movies = tools.make_dir(os.path.join(self.DESTINATION_FOLDER, 'Movies'))
        tools.make_dir(os.path.join(movies, 'Index'))
        assert os.path.exists(index_path)
        apply_index(self.DESTINATION_FOLDER, 'lol.json')
        assert dict_apply.called
        assert not os.path.exists(index_path)
