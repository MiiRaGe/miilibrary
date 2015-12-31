import os

from django.conf import settings

from factory import DjangoModelFactory, Sequence, SubFactory
from factory.fuzzy import FuzzyInteger, FuzzyChoice

from mii_sorter.models import Episode, Season, Serie


class SerieFactory(DjangoModelFactory):
    class Meta:
        model = Serie
        django_get_or_create = ('name',)

    name = FuzzyChoice(['Serie1', 'Serie2', 'Serie3'])


class SeasonFactory(DjangoModelFactory):
    class Meta:
        model = Season
        django_get_or_create = ('serie', 'number',)

    number = FuzzyInteger(low=1, high=10)
    serie = SubFactory(SerieFactory)


class EpisodeFactory(DjangoModelFactory):
    class Meta:
        model = Episode
        django_get_or_create = ('season', 'number',)

    number = FuzzyInteger(low=1, high=24)
    season = SubFactory(SeasonFactory)
    file_path = Sequence(lambda n: os.path.join(settings.DESTINATION_FOLDER, 'serie_%s.mkv' % n))
    file_size = FuzzyInteger(low=100, high=1000)
