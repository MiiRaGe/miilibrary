from django.contrib.admin import site, ModelAdmin
from mii_rss.models import FeedFilter

__author__ = 'MiiRaGe'


class FeedFilterAdmin(ModelAdmin):
    model = FeedFilter
    list_display = ('regex', 'name')


site.register(FeedFilter, FeedFilterAdmin)
