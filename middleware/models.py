import hashlib
import json
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.db.models import CharField, Model, DateTimeField, BinaryField

__author__ = 'MiiRaGe'


class JSONKeyValue(Model):
    type = CharField(max_length=40)
    key = CharField(max_length=100)
    date = DateTimeField()
    value = BinaryField()

    @staticmethod
    def set(type, key, value):
        '''
        This method transform a dict key, and dict value to hashed key, binary value.
        :param type:
        :param key:
        :param value:
        :return:
        '''
        hashed_key = JSONKeyValue._get_hashed_key(key)
        binary_value = JSONKeyValue._get_json_data(value)
        try:
            JSONKeyValue.objects.create(type=type, key=hashed_key, value=binary_value)
            return True
        except IntegrityError:
            return False

    @staticmethod
    def get(type, key):
        '''
        Get a value stored by hashing the key.
        :param type:
        :param key:
        :param value:
        :return:
        '''
        hashed_key = JSONKeyValue._get_hashed_key(key)
        try:
            value = JSONKeyValue.objects.get(type=type, key=hashed_key)
            return json.loads(value)
        except ObjectDoesNotExist:
            return None

    @staticmethod
    def _get_hashed_key(key):
        return hashlib.sha1(json.dumps(key)).hexdigests()

    @staticmethod
    def _get_json_data(value):
        return json.dumps(value).encode('utf-8')