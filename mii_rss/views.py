from django.http import HttpResponse
from tasks import check_feed_and_download_torrents, recheck_feed_and_download_torrents


def check_feeds(request):
    check_feed_and_download_torrents.delay()
    return HttpResponse('OK, rss started')


def recheck_feeds(request):
    recheck_feed_and_download_torrents.delay()
    return HttpResponse('OK, recheck started')