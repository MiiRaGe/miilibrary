from django.db.models import Model, CharField, DateTimeField
from django.utils import timezone

__author__ = 'MiiRaGe'


class Unpacked(Model):
    filename = CharField(max_length=255, unique=True)
    timestamp = DateTimeField(default=timezone.now)
