from django.contrib.admin import ModelAdmin
from django.contrib.admin import site
from mii_indexer.models import MovieRelation, Person, MovieTagging, Tag

__author__ = 'MiiRaGe'


class MovieRelationAdmin(ModelAdmin):
    model = MovieRelation
    list_display = ('movie', 'person', 'type')


class PersonAdmin(ModelAdmin):
    model = Person
    list_display = ('name',)


class MovieTaggingAdmin(ModelAdmin):
    model = MovieTagging
    list_display = ('movie', 'tag')


class TagAdmin(ModelAdmin):
    model = Tag
    list_display = ('name',)

site.register(MovieRelation)
site.register(Person)
site.register(MovieTagging)
site.register(Tag)
