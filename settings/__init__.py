# Then logic is base.py extends django.py and local.py needs to extends base.py
from local import *


if 'test' in sys.argv:
    SOURCE_FOLDER = relative('tests/test_input/')
    DESTINATION_FOLDER = relative('tests/test_output/')
    MONGO_DB_NAME += '_test'
    DATABASES['default']['engine'] = 'django.db.backends.sqlite3'