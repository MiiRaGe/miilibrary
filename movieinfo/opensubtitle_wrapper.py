import logging
import socket
import time

from xmlrpclib import ProtocolError, ServerProxy, SafeTransport, GzipDecodedResponse

from django.conf import settings
from pyexpat import ExpatError

logger = logging.getLogger(__name__)


class CustomTransport(SafeTransport):
    def parse_response(self, response):
        # read response data from httpresponse, and parse it

        # Check for new http response object, else it is a file object
        if hasattr(response, 'getheader'):
            if response.getheader("Content-Encoding", "") == "gzip":
                stream = GzipDecodedResponse(response)
            else:
                stream = response
        else:
            stream = response

        p, u = self.getparser()

        while 1:

            data = stream.read(1024)
            data = data.strip()
            if not data:
                break
            if self.verbose:
                print "body:", repr(data)
            try:
                p.feed(data)
            except ExpatError as e:
                import pdb;

                pdb.set_trace()
                print repr(e)
                pass

        if stream is not response:
            stream.close()
        p.close()

        return u.close()


class OpenSubtitleWrapper:
    def __init__(self):
        self.login_successful = False
        self.token = None
        self.server = None  # server initialized in log_in to avoid program not running offline

    def log_in(self, retry=False, max_retries=5):
        self.server = ServerProxy(settings.OPENSUBTITLE_API_URL, transport=CustomTransport())
        result = None
        go_on = True
        fail_count = 0
        while go_on:
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

    def get_imdb_information(self, imdb_id):
        if not self.login_successful:
            self.log_in()
            if not self.login_successful:
                return ''
        time.sleep(0.3)
        result = ''
        while True:
            try:
                result = self.server.GetIMDBMovieDetails(self.token, imdb_id)
                return result.get("data")
            except (ProtocolError):
                logger.info("Result :" + str(result))
                logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)

    def get_movie_names(self, movie_hashes):
        if not self.login_successful:
            self.log_in()
            if not self.login_successful:
                return ''
        return self.server.CheckMovieHash(self.token, movie_hashes).get("data")

    def get_movie_names2(self, movie_hashes):
        if not self.login_successful:
            self.log_in(True, 10)
            if not self.login_successful:
                return ''
        time.sleep(0.3)
        result = ''
        while True:
            try:
                result = self.server.CheckMovieHash2(self.token, movie_hashes)
                return result.get("data")
            except (ProtocolError):
                logger.info("Result : %s" % result)
                logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)

    def get_subtitles(self, movie_hash, movie_size, movie_name):
        if not self.login_successful:
            self.log_in()
            if not self.login_successful:
                return ''
        time.sleep(0.3)
        result = None
        while True:
            try:
                result = self.server.SearchSubtitles(self.token,
                                                     [
                                                         {'moviehash': movie_hash,
                                                          'moviebytesize': movie_size,
                                                          'sublanguageid': 'eng,fra,ger',
                                                          'query': movie_name}],
                                                     {'limit': 100})
                logger.debug(result)
                try:
                    result = result.get("data")
                except:
                    return None
                return result
            except ProtocolError:
                logger.info("Result : %s" % result)
                logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)
            except Exception as e:
                import pdb; pdb.set_trace()
                logger.exception(repr(e))
                return None


    def exit(self):
        return self.server.LogOut()
