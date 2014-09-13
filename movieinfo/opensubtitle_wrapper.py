'''
Created on 26 janv. 2014

@author: MiiRaGe
'''

import logging
import time
from xmlrpclib import ProtocolError, ServerProxy

import settings

logger = logging.getLogger("NAS")

class OpensubtitleWrapper:
    def __init__(self):
        self.login_successful = False
        self.token = None
        self.server = None  # server initialized in log_in to avoid program not running offline

    def log_in(self, retry=False, max_retries=10):
        self.server = ServerProxy("http://api.opensubtitles.org/xml-rpc")
        result = None
        go_on = True
        fail_count = 0
        while go_on:
            try:
                logger.info("Login into openSubtitle...")
                username = settings.OPENSUBTITLE_LOGIN
                password = settings.OPENSUBTITLE_PASSWORD
                result = self.server.LogIn(username, password, "gb", "miinaslibraryUA")
                self.token = result.get("token")
                status = result.get("status")
                if status.startswith('200'):
                    self.login_successful = True
                    return
            except (ProtocolError):
                logger.debug("Response : %s" % result)
                logger.info("Got rejected by the API, waiting 1minutes")
            fail_count += 1
            if not retry or fail_count == max_retries:
                self.login_successful = False
                return
            else:
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
                                                         {"moviehash": movie_hash,
                                                          "moviebytesize": movie_size,
                                                          "query": movie_name}],
                                                     {"limit": 100})
                logger.debug(result)
                result = result.get("data")
                return result
            except ProtocolError:
                logger.info("Result : %s" % result)
                logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)

    def exit(self):
        return self.server.LogOut()