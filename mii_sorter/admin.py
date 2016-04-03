from django.contrib.admin import ModelAdmin, site
from mii_sorter.models import Episode, Season, Serie, RegexRenaming

__author__ = 'MiiRaGe'


class SerieAdmin(ModelAdmin):
    model = Serie
    list_display = ('name',)


class SeasonAdmin(ModelAdmin):
    model = Season
    list_select_related = ('serie__name',)
    list_display = ('serie_name', 'number')
    list_filter = ('serie__name', 'number')

    def serie_name(self, obj):
        return obj.serie.name


class EpisodeAdmin(ModelAdmin):
    model = Episode
    list_select_related = ('season__serie__name', 'season__number')
    list_display = ('serie_name', 'season_number', 'number')
    list_filter = ('season__serie__name', 'season__number', 'number')

    def season_number(self, obj):
        return obj.season.number

    def serie_name(self, obj):
        return obj.season.serie.name


class RegexRenamingAdmin(ModelAdmin):
    model = RegexRenaming
    list_display = ('old', 'new')


site.register(Episode, EpisodeAdmin)
site.register(Season, SeasonAdmin)
site.register(Serie, SerieAdmin)
site.register(RegexRenaming, RegexRenamingAdmin)
