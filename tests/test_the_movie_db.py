import json
import responses

from django.test import TestCase

from movieinfo.the_movie_db_wrapper import TheMovieDBWrapper


@responses.activate
class TestOpenSubtitleWrapperLogin(TestCase):
    def setUp(self):
        self.tmdb = TheMovieDBWrapper()

    def test_get_movie_imdb_id(self):
        responses.add(responses.GET, '*',
                      body=json.dumps('test_passed'), status=200,
                      content_type='application/html')
        assert self.tmdb.get_movie_imdb_id('019283') == 'test_passed'

    def test_get_movie_name(self):
        return_value = {
            'results': [
                {'popularity': 1}
            ]
        }
        responses.add(responses.GET, '*',
                      body=json.dumps(return_value), status=200,
                      content_type='application/html')
        assert self.tmdb.get_movie_name('the dark knight', 2008) == return_value
