import mock
from django.conf import settings
from django.test import TestCase

from middleware.remote_execution import link, symlink, unrar, remove_dir


@mock.patch('middleware.remote_execution.shell_connection')
class TestRemoteExecution(TestCase):
    def test_link(self, shell):
        link('a', 'b')
        shell.run.assert_called_with(['ln', 'a', 'b'])

    def test_symlink(self, shell):
        symlink('a', 'b')
        shell.run.assert_called_with(['ln', '-s', 'a', 'b'])

    def test_unrar(self, shell):
        unrar('a', 'b')
        shell.run.assert_called_with([settings.REMOTE_UNRAR_PATH, 'e', '-y', 'a', 'b'])

    @mock.patch('middleware.remote_execution.delete_dir', new=mock.MagicMock())
    def test_remove_dir(self, shell):
        remove_dir('a')
        shell.run.assert_called_with(['rm', '-rf', 'a'])


class TestNonRemoteExecution(TestCase):
    @mock.patch('middleware.remote_execution.delete_dir')
    def test_remove_dir(self, delete_dir):
        remove_dir('a')
        delete_dir.assert_called_with('a')

    @mock.patch('middleware.remote_execution.os.symlink')
    def test_symlink(self, mocked_symlink):
        symlink('a', 'b')
        mocked_symlink.assert_called_with('a', 'b')

    @mock.patch('middleware.remote_execution.os.link')
    def test_link(self, mocked_link):
        link('a', 'b')
        mocked_link.assert_called_with('a', 'b')

    @mock.patch('middleware.remote_execution.subprocess')
    def test_unrar(self, mocked_subprocess):
        unrar('a', 'b')
        assert mocked_subprocess.check_output.called