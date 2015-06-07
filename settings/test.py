from local import *

SOURCE_FOLDER = relative('tests/test_input/')
DESTINATION_FOLDER = relative('tests/test_output/')
MONGO_DB_NAME += '_test'
DATABASES['default']['engine'] = 'django.db.backends.sqlite3'