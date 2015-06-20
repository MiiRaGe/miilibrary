from django.db.models import Model, CharField

__author__ = 'MiiRaGe'


class Unpacked(Model):
    filename = CharField(max_length='255', unique=True)