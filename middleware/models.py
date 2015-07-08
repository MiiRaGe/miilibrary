import hashlib
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import CharField, Model, DateTimeField, BinaryField
from django.utils import timezone

__author__ = 'MiiRaGe'


class JSONKeyValue(Model):
    type = CharField(max_length=40)
    key = CharField(max_length=50)
    date = DateTimeField()
    value = BinaryField()

    class Meta:
        unique_together = ('type', 'key')

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
        JSONKeyValue.objects.update_or_create(type=type, key=hashed_key, date=timezone.now(), value=binary_value)

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
            obj = JSONKeyValue.objects.get(type=type, key=hashed_key)
            return json.loads(obj.value)
        except ObjectDoesNotExist:
            return 0

    @staticmethod
    def _get_hashed_key(key):
        return hashlib.sha1(json.dumps(key)).hexdigest()

    @staticmethod
    def _get_json_data(value):
        return json.dumps(value).encode('utf-8')