from factory.django import DjangoModelFactory
from factory import  SubFactory
from factory.fuzzy import FuzzyChoice

from mii_indexer.models import MovieRelation, Person, MovieTagging, Tag
from mii_sorter.factories import MovieFactory


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = Person
        django_get_or_create = ('name',)

    name = FuzzyChoice(['actor1', 'actor2', 'actor3'])


class MovieRelationFactory(DjangoModelFactory):
    class Meta:
        model = MovieRelation
        django_get_or_create = ('movie', 'person', 'type',)

    type = FuzzyChoice(['Director', 'Actor'])
    movie = SubFactory(MovieFactory)
    person = SubFactory(PersonFactory)


class TagFactory(DjangoModelFactory):
    class Meta:
        model = Tag
        django_get_or_create = ('name',)

    name = FuzzyChoice(['Tag1', 'Tag2', 'Tag3'])


class MovieTaggingFactory(DjangoModelFactory):
    class Meta:
        model = MovieTagging
        django_get_or_create = ('movie', 'tag',)

    movie = SubFactory(MovieFactory)
    tag = SubFactory(TagFactory)
