import logging
import socket
import time
from xmlrpclib import ProtocolError, ServerProxy
from django.conf import settings

logger = logging.getLogger(__name__)


def needs_login(f):
    def wrapped_function(self, *args, **kwargs):
        if not self.login_successful:
            self.log_in()
            if not self.login_successful:
                return ''
        return f(self, *args, **kwargs)

    return wrapped_function


def retry_when_failing(f):
    def wrapped_function(*args, **kwargs):
        time.sleep(0.3)
        while True:
            try:
                result = f(*args, **kwargs)
                logger.debug(result)
                return result
            except ProtocolError:
                logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)
            except Exception as e:
                logger.exception(repr(e))
                return None

    return wrapped_function


class OpenSubtitleWrapper:
    def __init__(self):
        self.login_successful = False
        self.token = None
        self.server = None  # server initialized in log_in to avoid program not running offline

    def log_in(self, retry=False, max_retries=5):
        self.server = ServerProxy(settings.OPENSUBTITLE_API_URL)
        result = None
        fail_count = 0
        while True:
            try:
                logger.info("Login into openSubtitle...")
                username = settings.OPENSUBTITLE_LOGIN
                password = settings.OPENSUBTITLE_PASSWORD
                logger.warning('Trying to login')
                result = self.server.LogIn(username, password, "gb", "miinaslibraryUA")
                self.token = result.get("token")
                status = result.get("status")
                if status.startswith('200'):
                    self.login_successful = True
                    return
            except ProtocolError:
                logger.debug("Response : %s" % result)
                logger.info("Got rejected by the API, waiting 1minutes")
            except (socket.gaierror, socket.timeout):
                logger.warning("Can't communicate with server")
                return

            fail_count += 1
            if not retry or fail_count == max_retries:
                self.login_successful = False
                return
            time.sleep(60)

    @needs_login
    @retry_when_failing
    def get_imdb_information(self, imdb_id):
        return self.server.GetIMDBMovieDetails(self.token, imdb_id).get('data')

    @needs_login
    @retry_when_failing
    def get_movie_names(self, movie_hashes):
        return self.server.CheckMovieHash(self.token, movie_hashes).get('data')

    @needs_login
    @retry_when_failing
    def get_movie_names2(self, movie_hashes):
        return self.server.CheckMovieHash2(self.token, movie_hashes).get('data')

    @needs_login
    @retry_when_failing
    def get_subtitles(self, movie_hash, movie_size, movie_name):
        return self.server.SearchSubtitles(self.token,
                                           [
                                               {'moviehash': movie_hash,
                                                'moviebytesize': movie_size,
                                                'sublanguageid': 'eng,fra,ger',
                                                'query': movie_name}
                                           ],
                                           {'limit': 100}).get('data')

    @needs_login
    def exit(self):
        return self.server.LogOut()
