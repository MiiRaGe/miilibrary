import errno
import mock
import os

from pyfakefs.fake_filesystem_unittest import TestCase as FakeFSTestCase
from unittest import TestCase

from mii_common.tools import make_dir, delete_dir, listdir_abs, dict_apply, link_or_copy, relative_symlink, \
    safe_delete, unrar, check_mounted, LibraryNotMounted
from settings.base import env_bool


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

    def test_relative_symlink(self):
        os.makedirs('/test/a/b')
        relative_symlink('/t/blah.mkv', '/test/a/b/blah.mkv')
        assert os.readlink('/test/a/b/blah.mkv') == '../../../t/blah.mkv'
        assert os.path.exists('/test/a/b/blah.mkv')

    def test_safe_delete_dangling_symlink(self):
        os.symlink('/t/missing.mkv', '/test/dangling.mkv')
        safe_delete('/test/dangling.mkv')
        assert not os.path.lexists('/test/dangling.mkv')

    def test_link_or_copy_same_filesystem(self):
        link_or_copy('/t/blah.mkv', '/test/blah.mkv', '/test/.staging')
        assert os.stat('/test/blah.mkv').st_nlink == 2
        assert not os.path.exists('/test/.staging')

    def test_link_or_copy_other_filesystem(self):
        with mock.patch('mii_common.tools.os.link', side_effect=OSError(errno.EXDEV, 'Invalid cross-device link')):
            link_or_copy('/t/blah.mkv', '/test/blah.mkv', '/test/.staging')
        assert os.stat('/test/blah.mkv').st_nlink == 1
        assert os.listdir('/test/.staging') == []

    def test_link_or_copy_unexpected_error(self):
        with mock.patch('mii_common.tools.os.link', side_effect=OSError(errno.ENOSPC, 'No space left on device')):
            with self.assertRaises(OSError):
                link_or_copy('/t/blah.mkv', '/test/blah.mkv', '/test/.staging')


class TestUnrar(TestCase):
    @mock.patch('mii_common.tools.subprocess')
    def test_unrar_paths_with_spaces(self, subprocess):
        unrar('/raw/My Movie (2011)/movie.rar', '/processed/.incoming/tmp')
        subprocess.check_output.assert_called_with(
            ['unrar', 'e', '-y', '/raw/My Movie (2011)/movie.rar', '/processed/.incoming/tmp/'])

    def test_check_mounted(self):
        assert check_mounted('/') == '/'
        for path in ('', 'test', '/not_mounted_miilibrary'):
            with self.assertRaises(LibraryNotMounted):
                check_mounted(path)


class TestSettings(TestCase):
    def test_env_bool(self):
        for value, expected in (('False', False), ('0', False), ('', False), ('true', True), ('1', True)):
            with mock.patch.dict('settings.base.environ', {'FLAG': value}):
                assert env_bool('FLAG', True) is expected
        with mock.patch.dict('settings.base.environ', {}, clear=True):
            assert env_bool('FLAG', True) is True
