from django.db.models import Model, IntegerField, CharField

__author__ = 'MiiRaGe'


class FeedDownloaded(Model):
    season = IntegerField()
    episode = IntegerField()
    re_filter = CharField(max_length=100)

    class Meta:
        unique_together = [
            'season', 'episode', 're_filter'
        ]