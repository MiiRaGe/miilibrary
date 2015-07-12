import json
from django.test import TestCase
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

    def test_set_data_type(self):
        JSONKeyValue.set(self.type1, self.key1, self.data1)
        object = JSONKeyValue.objects.get(type=self.type1)
        self.assertEqual(object.key_text, json.dumps(self.key1))