import json
import mock

from django.test import TestCase

from middleware.mii_cache_wrapper import MiiCachedData
from middleware.models import JSONKeyValue

__author__ = 'MiiRaGe'


class TestJSONKeyValue(TestCase):
    def setUp(self):
        self.type1 = 'type1'
        self.type2 = 'type2'
        self.key1 = 'key1'
        self.key2 = 'key2'
        self.data1 = [1, 2, 3]
        self.data2 = {'name': 'value', 'value': [1, 2, 3]}

    def test_get_no_data(self):
        self.assertEqual(JSONKeyValue.get(self.type1, self.key1), 0)

    def test_set_data(self):
        JSONKeyValue.set(self.type1, self.key1, self.data1)
        JSONKeyValue.set(self.type1, self.key2, self.data2)
        self.assertEqual(JSONKeyValue.get(self.type1, self.key1), self.data1)
        self.assertEqual(JSONKeyValue.get(self.type1, self.key2), self.data2)

    def test_set_data_type(self):
        JSONKeyValue.set(self.type1, self.key1, self.data1)
        JSONKeyValue.set(self.type2, self.key1, self.data2)
        self.assertEqual(JSONKeyValue.get(self.type1, self.key1), self.data1)
        self.assertEqual(JSONKeyValue.get(self.type2, self.key1), self.data2)

    def test_set_duplicate(self):
        JSONKeyValue.set(self.type1, self.key1, self.data1)
        JSONKeyValue.set(self.type1, self.key1, self.data2)

    def test_key_text(self):
        JSONKeyValue.set(self.type1, self.key1, self.data1)
        object = JSONKeyValue.objects.get(type=self.type1)
        self.assertEqual(object.key_text, json.dumps(self.key1))


class TestMiiMongoStored(TestCase):
    def setUp(self):
        class test(MiiCachedData):
            mapping = {
                'test_function': lambda x: {'result': 'fake'},
            }
            type = 'test'

            def test(self):
                self.key = {'name': 'blah'}
                return self.get_or_sync('test_function', 'arg')

        self.cached_functions = test()

    @mock.patch('middleware.models.JSONKeyValue.get')
    @mock.patch('middleware.models.JSONKeyValue.set')
    def test_caching_calls(self, set, get):
        get.return_value = 0
        self.cached_functions.test()
        assert set.called
        set.called = False
        get.return_value = 1
        self.cached_functions.test()
        assert not set.called
