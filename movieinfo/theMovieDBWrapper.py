'''
Created on 26 janv. 2014

@author: MiiRaGe
'''
import re,cgi
try:
    print("Trying to import json (2.6+)")
    import json
except:
    print("Failed, fallbacking to simplejson (install if not already done)")
    import simplejson as json
    
from urllib2 import Request, urlopen, HTTPError
        
class TheMovieDBWrapper:
    
    def __init__(self):
        self.headers = {"Accept": "application/json"}
        self.server = 'http://api.themoviedb.org/'
        self.api_key = '?api_key=9a35d9bef7cbb4fc7355bf143f8560b4'

    def getMovieName(self,moviename,year):
        moviename = re.sub(" +","+",moviename)
        searchRequest = Request(self.server + "3/search/movie"+ self.api_key+ "&query="  +cgi.escape(moviename)+"&year=" + year , headers=self.headers  )
        try:
            response_body = urlopen(searchRequest).read()
        except(HTTPError):
            return False
        response = json.loads(response_body)
        return response.get("results")
        
    def get_movie_imdb_id(self,movieId):
        searchRequest = Request(self.server + "3/movie/" +movieId + self.api_key, headers=self.headers)
        try:
            response_body = urlopen(searchRequest).read()
            response = json.loads(response_body)
            return response
        except(HTTPError):
            return False
