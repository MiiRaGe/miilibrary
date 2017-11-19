from django.contrib.admin import ModelAdmin
from django.contrib.admin import site
from mii_unpacker.models import Unpacked

__author__ = 'MiiRaGe'


class UnpackedAdmin(ModelAdmin):
    model = Unpacked
    list_display = ('filename', 'timestamp')


site.register(Unpacked, UnpackedAdmin)
