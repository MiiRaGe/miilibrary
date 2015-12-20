!#/usr/bin/python
import json
import os
import shutil
import settings

from mii_common import tools

json_file_path = os.path.join(settings.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
if __name__ == '__main__' and os.path.exists(json_file_path):
    with open(json_file_path, 'rb') as inputfile:
        dict_index = json.load(inputfile)

    index_path = os.path.join(settings.DESTINATION_FOLDER, 'Movies', 'Index')
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
    current_path_root = tools.make_dir(index_path)
    tools.dict_apply(current_path_root, dict_index, symlink_method=os.symlink)
    os.remove(json_file_path)
