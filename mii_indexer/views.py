from django.http import HttpResponse

from mii_indexer.tasks import index_movies


def start_index(request):
    index_movies.delay()
    return HttpResponse('OK, unpack sort index started')