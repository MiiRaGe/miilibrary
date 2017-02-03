#!/usr/bin/python
import json
import os
import shutil
import settings

from raven import Client

client = Client(settings.SENTRY_URL)

from mii_common import tools
from time import sleep


def apply_index(path, json_file_name):
    json_file_path = os.path.join(path, json_file_name)
    if not os.path.exists(json_file_path):
        return
    with open(json_file_path, 'rb') as inputfile:
        input_json = inputfile.read().decode('utf8')
        dict_index = json.loads(input_json)
    client.captureMessage(u'Opened the json file')
    index_path = os.path.join(path, 'Movies', 'Index')
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
    retry = 0
    while os.path.exists(index_path):
        retry += 1
        client.captureMessage(u'Sleeping until deleted')
        sleep(10)
        if retry == 5:
            return

    current_path_root = tools.make_dir(index_path)
    tools.dict_apply(current_path_root, dict_index, symlink_method=os.symlink)
    os.remove(json_file_path)

if __name__ == '__main__':
    try:
        apply_index(settings.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
    except Exception:
        client.captureException()
