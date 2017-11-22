from django.contrib.admin import ModelAdmin
from django.contrib.admin import site
from mii_indexer.models import MovieRelation, Person, MovieTagging, Tag

__author__ = 'MiiRaGe'


class MovieRelationAdmin(ModelAdmin):
    model = MovieRelation
    list_display = ('movie', 'person', 'type')
    list_filter = ('movie__title', 'movie__year', 'movie__indexed', 'person__name', 'type')
    list_select_related = ('movie', 'person')


class PersonAdmin(ModelAdmin):
    model = Person
    list_display = ('name',)


class MovieTaggingAdmin(ModelAdmin):
    model = MovieTagging
    list_display = ('movie', 'tag')
    list_filter = ('tag__name', 'movie__title', 'movie__year', 'movie__indexed')
    list_select_related = ('movie', 'tag')


class TagAdmin(ModelAdmin):
    model = Tag
    list_display = ('name',)

site.register(MovieRelation)
site.register(Person)
site.register(MovieTagging)
site.register(Tag)
