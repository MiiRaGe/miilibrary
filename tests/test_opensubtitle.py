import mock
import socket
from xmlrpclib import ProtocolError
from django.test import override_settings, TestCase
from movieinfo.opensubtitle_wrapper import OpenSubtitleWrapper, needs_login, retry_when_failing

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
        fake_server.LogIn.side_effect = ProtocolError(u'', '', '', '')
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
        fake_server.LogIn.side_effect = ProtocolError(u'', '', '', '')
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
        assert self.os.get_subtitles('', '', '') == 'info'


class TestOpenSubtitleWrapperDecorators(TestCase):
    def test_true_login(self):
        class Dummy:
            login_successful = False

            @needs_login
            def t(self):
                return 'Test Passed'

            def log_in(self):
                self.login_successful = True

        assert Dummy().t() == 'Test Passed'

    def test_login_broken(self):
        class Dummy:
            login_successful = False

            @needs_login
            def t(self):
                return 'Test Passed'

            def log_in(self):
                pass

        assert Dummy().t() == ''

    @mock.patch('movieinfo.opensubtitle_wrapper.time.sleep')
    def test_retry_while_failing(self, sleep):
        class Dummy:
            count = 0

            @retry_when_failing
            def t(self):
                if self.count < 2:
                    self.count += 1
                    raise ProtocolError(u'', '', '', '')
                else:
                    return 'Test Passed'

        assert Dummy().t() == 'Test Passed'
        assert sleep.call_count == 2

    @mock.patch('movieinfo.opensubtitle_wrapper.time.sleep')
    def test_retry_while_failing_unknown_error(self, sleep):
        class Dummy:
            @retry_when_failing
            def t(self):
                raise Exception('Unknown error')

        assert Dummy().t() is None
