from django.http import HttpResponse
from mii_unpacker.tasks import unpack


def start_unpacker(request):
    unpack.delay()
    return HttpResponse('OK, sort started')