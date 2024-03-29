import mock
import os

from pyfakefs.fake_filesystem_unittest import TestCase as FakeFSTestCase
from unittest import TestCase

from mii_common.tools import make_dir, delete_dir, listdir_abs, dict_apply


@mock.patch('mii_common.tools.os')
class TestTools(TestCase):
    def test_make_dir(self, os):
        make_dir('/test_dir/')
        os.mkdir.assert_called_with('/test_dir/')

    @mock.patch('mii_common.tools.logger')
    def test_make_dir_unexpected_error(self, logger, os):
        os.mkdir.side_effect = OSError()
        make_dir('/test_dir/')
        os.mkdir.assert_called_with('/test_dir/')
        assert logger.warning.called


class TestWithFakeFS(FakeFSTestCase):
    def setUp(self):
        self.setUpPyfakefs()
        self.fs.create_file('/t/blah.mkv')
        os.mkdir('/test/')

    def test_delete_dir(self):
        self.fs.create_file('/t/e/s/t/blah.mkv')
        self.fs.create_file('/t/e/s/blah.mkv')
        self.fs.create_file('/t/e/t/blah.mkv')
        delete_dir('/t/e/')
        assert not os.path.exists('/t/e')

    def test_delete_dir_excluding_root(self):
        self.fs.create_file('/t/e/s/t/blah.mkv')
        self.fs.create_file('/t/e/s/blah.mkv')
        self.fs.create_file('/t/e/t/blah.mkv')
        delete_dir('/t/e/', include_root=False)
        assert not os.listdir('/t/e')

    def test_listdirabs(self):
        assert listdir_abs('/t') == ['/t/blah.mkv']

    def test_dict_apply(self):
        dict_apply('/test', {'a': {'b': [('blah', '/t/blah.mkv')]}})
        assert os.path.exists('/test/a/b/blah')

    def test_dict_apply_empty_leaf(self):
        dict_apply('/test', {'a': {'b': [('blah', '/t/blah.mkv')], 'c': []}})
        assert os.path.exists('/test/a/b/blah')
        assert not os.path.exists('/test/a/c/')

    def test_dict_apply_custom_symlink(self):
        def custom_symlink(source, destination):
            destination += '.symlink'
            os.symlink(source, destination)

        dict_apply('/test/', {'a': {'b': [('blah', '/t/blah.mkv')]}}, symlink_method=custom_symlink)
        assert os.path.exists('/test/a/b/blah.symlink')

    @mock.patch('mii_common.tools.logger')
    def test_dict_apply_custom_symlink_raises_error(self, logger):
        def custom_symlink(source, destination):
            destination += '.symlink'
            raise OSError()

        dict_apply('/test', {'a': {'b': [('blah', '/t/blah.mkv')]}}, symlink_method=custom_symlink)
        assert not os.path.exists('/test/a/b/blah.symlink')
        assert logger.error.called
        assert logger.error.call_count == 2

    def test_dict_apply_empty_dict(self):
        before = os.listdir('/test')
        dict_apply('/test', {})
        after = os.listdir('/test')
        assert before == after
