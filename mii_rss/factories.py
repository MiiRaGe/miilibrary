from datetime import timedelta

from django.utils import timezone
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyInteger, FuzzyChoice, FuzzyDateTime

from mii_rss.models import FeedDownloaded, FeedEntries, FeedFilter


class FeedDownloadedFactory(DjangoModelFactory):
    class Meta:
        model = FeedDownloaded
        django_get_or_create = ('re_filter', 'season', 'episode',)

    season = FuzzyInteger(0, 20)
    episode = FuzzyInteger(0, 20)
    re_filter = FuzzyChoice(['Serie1', 'Serie2', 'Serie3'])


class FeedEntriesFactory(DjangoModelFactory):
    class Meta:
        model = FeedEntries
    json_entries = '{"entries": [{"link": "/file.torrent?", "title": "file"}]}'
    date = FuzzyDateTime(timezone.now() - timedelta(days=2))


class FeedFilterFactory(DjangoModelFactory):
    class Meta:
        model = FeedFilter

    regex = ''
    name = ''
