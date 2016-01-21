import json
import mock

from django.test import TestCase
from urllib2 import HTTPError

from movieinfo.the_movie_db_wrapper import TheMovieDBWrapper


@mock.patch('movieinfo.the_movie_db_wrapper.urlopen')
class TestOpenSubtitleWrapperLogin(TestCase):
    def setUp(self):
        self.tmdb = TheMovieDBWrapper()

    def test_get_movie_imdb_id(self, urlopen):
        urlopen.return_value = mock.MagicMock(read=mock.MagicMock(return_value=json.dumps('test_passed')))
        assert self.tmdb.get_movie_imdb_id('019283') == 'test_passed'

    def test_get_movie_name(self, urlopen):
        return_value = {
            'results': [
                {'popularity': 1}
            ]
        }
        urlopen.return_value = mock.MagicMock(read=mock.MagicMock(return_value=json.dumps(return_value)))
        assert self.tmdb.get_movie_name('the dark knight', 2008) == return_value

    def test_get_url_error(self, urlopen):
        urlopen.return_value = mock.MagicMock(read=mock.MagicMock(side_effect=HTTPerror(u'', '', '', '', None)))
        assert self.tmdb.get_url('') is False
