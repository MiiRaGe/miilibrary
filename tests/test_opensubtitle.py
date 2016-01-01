import mock
import socket

from xmlrpclib import ProtocolError
from django.test import override_settings, TestCase

from movieinfo.opensubtitle_wrapper import OpenSubtitleWrapper


fake_server = mock.MagicMock()


@override_settings(OPENSUBTITLE_LOGIN='', OPENSUBTITLE_PASSWORD='', OPENSUBTITLE_API_URL='')
@mock.patch('movieinfo.opensubtitle_wrapper.ServerProxy', new=mock.MagicMock(return_value=fake_server))
class TestOpenSubtitleWrapperLogin(TestCase):
    def setUp(self):
        self.os = OpenSubtitleWrapper()

    def test_simple_login(self):
        fake_server.LogIn.return_value = {
            'status': '200',
            'token': 'token'
        }
        self.os.log_in()
        assert self.os.token
        assert self.os.login_successful

    def test_simple_login_error(self):
        fake_server.LogIn.side_effect = ProtocolError('', '', '', '')
        self.os.log_in(retry=False)
        assert not self.os.token
        assert not self.os.login_successful

    def test_simple_login_error_socket(self):
        fake_server.LogIn.side_effect = socket.gaierror
        self.os.log_in()
        assert not self.os.token
        assert not self.os.login_successful

    @mock.patch('movieinfo.opensubtitle_wrapper.time.sleep')
    def test_simple_login_error_with_retry(self, sleep):
        fake_server.LogIn.side_effect = ProtocolError('', '', '', '')
        self.os.log_in(retry=True, max_retries=3)
        assert not self.os.token
        assert not self.os.login_successful
        assert sleep.call_count == 2

    def test_logout(self):
        self.os.log_in(retry=False)
        self.os.exit()
        assert fake_server.LogOut.called


class TestOpenSubtitleWrapper(TestCase):
    def setUp(self):
        self.os = OpenSubtitleWrapper()
        self.os.login_successful = True
        self.os.token = 'token'
        self.os.server = fake_server

    def test_get_imdb_information(self):
        fake_server.GetIMDBMovieDetails.return_value = {'data': 'info'}
        assert self.os.get_imdb_information('imdb_id') == 'info'

    def test_get_moviehash_information(self):
        fake_server.CheckMovieHash.return_value = {'data': 'info'}
        assert self.os.get_movie_names(['hash']) == 'info'

    def test_get_moviehash2_information(self):
        fake_server.CheckMovieHash2.return_value = {'data': 'info'}
        assert self.os.get_movie_names2(['hash']) == 'info'

    def test_getsubtitles_information(self):
        fake_server.SearchSubtitles.return_value = {'data': 'info'}
        assert self.os.get_subtitles('','','') == 'info'


class TestOpenSubtitleWrapperDecorators(TestCase):
    def setUp(self):
        pass

    # @mock.patch('movieinfo.opensubtitle_wrapper.time.sleep')
    # def test_get_imdb_information_fail_once(self, sleep):
    #     fake_server.GetIMDBMovieDetails.side_effect = [ProtocolError('', '', '', ''), {'data': 'info'}]
    #     assert self.os.get_imdb_information('imdb_id') == 'info'
    #     assert sleep.called
    #