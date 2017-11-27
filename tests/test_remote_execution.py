import mock
from django.conf import settings
from django.test import TestCase

from middleware.remote_execution import link, symlink, unrar, remove_dir


@mock.patch('middleware.remote_execution.ShellConnection')
class TestRemoteExecution(TestCase):
    def test_link(self, shell):
        link('', '')
        shell.run.assert_called_with(['ln', '', ''])

    def test_symlink(self, shell):
        symlink('', '')
        shell.run.assert_called_with(['ln', '-s', '', ''])

    def test_unrar(self, shell):
        unrar('', '')
        shell.run.assert_called_with([settings.REMOTE_UNRAR_PATH, 'e', '-y', '', ''])

    @mock.patch('middleware.remote_execution.delete_dir', new=mock.MagicMock())
    def test_remove_dir(self, shell):
        remove_dir('')
        shell.run.assert_called_with(['rm', '-rf', ''])


class TestNonRemoteExecution(TestCase):
    @mock.patch('middleware.remote_execution.delete_dir')
    def test_remove_dir(self, delete_dir):
        remove_dir('')
        delete_dir.assert_called_with('')

    @mock.patch('middleware.remote_execution.os.symlink')
    def test_symlink(self, mocked_symlink):
        symlink('', '')
        mocked_symlink.assert_called_with('', '')

    @mock.patch('middleware.remote_execution.os.link')
    def test_link(self, mocked_link):
        link('', '')
        mocked_link.assert_called_with('', '')

    @mock.patch('middleware.remote_execution.subprocess')
    def test_unrar(self, mocked_subprocess):
        unrar('', '')
        assert mocked_subprocess.check_output.called