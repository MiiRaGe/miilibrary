from django.contrib.admin import site
from mii_indexer.models import MovieRelation, Person, MovieTagging, Tag

__author__ = 'MiiRaGe'


site.register(MovieRelation)
site.register(Person)
site.register(MovieTagging)
site.register(Tag)
