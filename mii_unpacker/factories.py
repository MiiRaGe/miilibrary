from factory import DjangoModelFactory, Sequence

from mii_unpacker.models import Unpacked


class UnpackedFactory(DjangoModelFactory):
    class Meta:
        model = Unpacked

    filename = Sequence(lambda n: 'filename_%s.mkv' % n)
