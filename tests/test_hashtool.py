import mock

from pyfakefs.fake_filesystem_unittest import TestCase

from movieinfo.hash_tool import hash_file


class TestHashTool(TestCase):
    def setUp(self):
        self.setUpPyfakefs()

    def test_hash_file(self):
        self.fs.CreateFile('/test', contents='con' * 65535)
        assert hash_file('/test') == '6873746873774dab'

    def test_hash_file_size_error(self):
        self.fs.CreateFile('/test', contents='c')
        assert hash_file('/test') == 'SizeError'

    @mock.patch('movieinfo.hash_tool.struct')
    def test_hash_file_ioerror(self, struct):
        struct.calcsize.side_effect = IOError
        self.fs.CreateFile('/test', contents='c')
        assert hash_file('/test') == 'IOError'


