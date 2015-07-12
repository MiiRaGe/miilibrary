import hashlib
import json

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import CharField, Model, DateTimeField, BinaryField
from django.utils import timezone

__author__ = 'MiiRaGe'


class JSONKeyValue(Model):
    type = CharField(max_length=40)
    key = CharField(max_length=50)
    key_text = CharField(max_length=200, default='')
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
        hashed_key, json_key = JSONKeyValue._get_hashed_key(key)
        binary_value = JSONKeyValue._get_json_data(value)
        JSONKeyValue.objects.update_or_create(type=type, key=hashed_key, defaults={'date': timezone.now(),
                                                                                   'value': binary_value,
                                                                                   'key_text': json_key,
                                                                                   })

    @staticmethod
    def get(type, key):
        '''
        Get a value stored by hashing the key.
        :param type:
        :param key:
        :param value:
        :return:
        '''
        hashed_key, json_key = JSONKeyValue._get_hashed_key(key)
        try:
            obj = JSONKeyValue.objects.get(type=type, key=hashed_key)
            return json.loads(obj.value)
        except ObjectDoesNotExist:
            return 0

    @staticmethod
    def _get_hashed_key(key):
        key_json = json.dumps(key)
        return hashlib.sha1(key_json).hexdigest(), key_json

    @staticmethod
    def _get_json_data(value):
        return json.dumps(value).encode('utf-8')