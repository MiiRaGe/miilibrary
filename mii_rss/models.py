from django.db.models import Model, IntegerField, CharField, TextField, DateTimeField
from django.utils import timezone


class FeedDownloaded(Model):
    season = IntegerField()
    episode = IntegerField()
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