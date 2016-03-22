from base import *

DATABASES['default'] = {
    'ENGINE': 'django.db.backends.sqlite3',
    'NAME': 'test_db.db'
}

REMOTE_FILE_OPERATION_ENABLED = False