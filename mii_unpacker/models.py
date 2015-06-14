from django.db.models import Model, TextField

__author__ = 'MiiRaGe'


class Unpacked(Model):
    filename = TextField(max_length='400', unique=True)