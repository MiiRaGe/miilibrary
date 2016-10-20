from django.http import HttpResponse

from mii_indexer.tasks import index_movies, apply_local_index


def start_index(request):
    index_movies.delay()
    return HttpResponse(u'OK, index started\n')


def start_apply_index(request):
    apply_local_index.delay()
    return HttpResponse(u'OK, apply index started\n')
