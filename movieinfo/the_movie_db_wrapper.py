import cgi
import json
import re

from urllib2 import Request, urlopen, HTTPError


class TheMovieDBWrapper:
    def __init__(self):
        self.server = 'http://api.themoviedb.org'
        self.api_key = 'api_key=9a35d9bef7cbb4fc7355bf143f8560b4'

    def get_movie_name(self, movie_name, year):
        movie_name = re.sub("\s+", "+", movie_name)
        url = "%s/3/search/movie?%s&query=%s" % (self.server, self.api_key, cgi.escape(movie_name))
        if year:
            url += "&year=%s" % year
        results = self.get_url(url)
        results['results'] = sorted(results['results'], key=(lambda x: x['popularity']), reverse=True)
        return results

    def get_movie_imdb_id(self, movie_id):
        url = "%s/3/movie/%s?%s" % (self.server, movie_id, self.api_key)
        return self.get_url(url)

    @staticmethod
    def get_url(url):
        search_request = Request(url, headers={"Accept": "application/json"})
        try:
            response_body = urlopen(search_request).read()
        except HTTPError:
            return False
        return json.loads(response_body)
