from factory.django import DjangoModelFactory
from factory import  Sequence

from mii_unpacker.models import Unpacked


class UnpackedFactory(DjangoModelFactory):
    class Meta:
        model = Unpacked

    filename = Sequence(lambda n: 'filename_%s.mkv' % n)
