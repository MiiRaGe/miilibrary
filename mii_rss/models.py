from django.db.models import Model, IntegerField, CharField, TextField, DateTimeField
from django.utils import timezone


class FeedDownloaded(Model):
    season = IntegerField()
    episode = IntegerField(null=True)
    re_filter = CharField(max_length=100)

    class Meta:
        unique_together = [
            'season', 'episode', 're_filter'
        ]


class FeedEntries(Model):
    json_entries = TextField()
    date = DateTimeField(default=timezone.now)

    class Meta:
        get_latest_by = 'date'


class FeedItem(Model):
    # One row per torrent seen in the feeds (FeedEntries is the raw dump of each fetch), kept until clean_history.
    link_hash = CharField(max_length=56, unique=True)
    title = TextField()
    link = TextField()
    date = DateTimeField(default=timezone.now, db_index=True)
    added = DateTimeField(null=True, blank=True)


class FeedFilter(Model):
    regex = CharField(max_length=255)
    name = CharField(max_length=255, unique=True)
