#!/usr/bin/python
import json
import os
import settings
import random
import logging

from mii_common import tools

i = random.randint(0, 100)
LOG_FILENAME = 'apply_index_{}.log'.format(i)

logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


def apply_index(path, json_file_name):
    json_file_path = os.path.join(path, json_file_name)
    if not os.path.exists(json_file_path):
        return
    with open(json_file_path, 'rb') as inputfile:
        input_json = inputfile.read().decode('utf8')
        dict_index = json.loads(input_json)
    try:
        with open(json_file_path + '.old', 'rb') as inputfile:
            input_json = inputfile.read().decode('utf8')
            old_dict_index = json.loads(input_json)
    except IOError:
        old_dict_index = {}
    if dict_index == old_dict_index:
        os.remove(json_file_path)
    else:
        index_path = os.path.join(path, 'Movies', 'Index')
        current_path_root = tools.make_dir(index_path)
        tools.dict_apply(current_path_root, dict_index, symlink_method=os.symlink)
        if os.path.exists(json_file_path + '.old'):
            os.remove(json_file_path + '.old')
        os.rename(json_file_path, json_file_path + '.old')


if __name__ == '__main__':
    try:
        apply_index(settings.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
    except Exception as e:
        logging.exception('Failed {}'.format(repr(e)))
