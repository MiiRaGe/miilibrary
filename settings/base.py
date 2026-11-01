# Import the configuration settings file - REPLACE projectname with your project
config_module = __import__('settings.django', globals(), locals(), 'django')

# Load the config settings properties into the local scope.
for setting in dir(config_module):
    if setting == setting.upper():
        locals()[setting] = getattr(config_module, setting)

from settings.django import DATABASES, CACHES
from os import environ
from celery.schedules import crontab
from settings.base import ALLOWED_HOSTS


def env_bool(name, default):
    # bool('False') is True, so parse the usual spellings explicitly
    return environ.get(name, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


#MiiNASLibrary configuration file

"""Configuration file"""
# Both are only needed by the filesystem worker, and must be absolute paths of mounted folders.
#This Folder is browsed recursively for .rar files and movie files (mkv,avi...): the completed torrents
SOURCE_FOLDER = environ.get('SOURCE_FOLDER', '')

#This is the root of the media folder (destination)
DESTINATION_FOLDER = environ.get('DESTINATION_FOLDER', '')

"""[Unpacking]"""
#Minimum size to be considered as non sample (in MB)
MINIMUM_SIZE = 125

"""[OpenSubtitle]"""
OPENSUBTITLE_API_URL = environ.get('OPENSUBTITLE_API_URL', "https://api.opensubtitles.org/xml-rpc")
OPENSUBTITLE_LOGIN = environ.get('OPENSUBTITLE_LOGIN', '')
OPENSUBTITLE_PASSWORD = environ.get('OPENSUBTITLE_PASSWORD', '')


"""[RSS Link]"""
RSS_URL = environ.get('RSS_URL', 'http://www.torrentday.com/torrents/rss?download;l7;u=xxx;tp=xxx')

"""[Django Databases]"""
DATABASES['default']['NAME'] = environ.get('DB_NAME', 'media')
DATABASES['default']['USER'] = environ.get('DB_USER', 'MiiRaGe')
DATABASES['default']['PASSWORD'] = environ.get('DB_PASSWORD', '1234')
DATABASES['default']['HOST'] = environ.get('DB_HOST', 'localhost')
DATABASES['default']['PORT'] = environ.get('DB_PORT', '')
DATABASES['default']['ENGINE'] = environ.get('DB_ENGINE', 'django.db.backends.sqlite3')

"""[Django Caches]"""
# Shared by every worker: it holds the single instance task locks. Must be a redis:// url.
CACHES['default']['LOCATION'] = environ.get('CACHE_LOCATION', 'redis://127.0.0.1:6379')

"""[Django Secrets]"""
SECRET_KEY = environ.get('SECRET_KEY', '+^(g2=uuez(s1qgpmznc&amp;zx4win6o36*9d$7l=5!)tf77*110c')

"""[Django Origins]"""
CSRF_TRUSTED_ORIGINS = [u'https://' + environ.get('EXTRA_ALLOWED_HOST', u'localhost'), u'http://' + environ.get('EXTRA_ALLOWED_IP', u'127.0.0.1') ]

"""Celery Broker"""
BROKER_URL = environ.get('BROKER_URL', 'amqp://guest:**@localhost:5672//')
CELERY_BROKER_URL = BROKER_URL

"""Celery task routing"""
# Tasks touching the media files are sent to this queue, consumed by the worker running next to the storage (the NAS)
# where every file operation is a local POSIX call. The other tasks (rss, transmission, history) stay on the default
# "celery" queue and can run anywhere (e.g. the kubernetes cluster).
FILESYSTEM_QUEUE = environ.get('FILESYSTEM_QUEUE', 'filesystem')
CELERY_TASK_ROUTES = {task_name: {'queue': FILESYSTEM_QUEUE} for task_name in (
    'mii_unpacker.tasks.unpack',
    'mii_sorter.tasks.sort',
    'mii_indexer.tasks.index_movies',
    'mii_interface.tasks.check_library',
)}
# The broker lives on another machine, keep retrying instead of crashing the worker when it's not up yet.
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
# Synced into the django_celery_beat tables by the database scheduler. Before the 6am unpack/sort so moved back
# orphan folders get sorted again.
CELERY_BEAT_SCHEDULE = {
    'check_library': {
        'task': 'mii_interface.tasks.check_library',
        'schedule': crontab(hour=5, minute=30),
    },
}

REPORT_ENABLED = env_bool('REPORT_ENABLED', True)

# Django-dbbackup settings (django-dbbackup >= 5 reads its storage from STORAGES)
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    'dbbackup': {
        'BACKEND': environ.get('DBBACKUP_STORAGE', 'django.core.files.storage.FileSystemStorage'),
        'OPTIONS': {'location': environ.get('DBBACKUP_BACKUP_DIRECTORY', '/tmp/backup/')},
    },
}

SENTRY_URL = environ.get('SENTRY_URL', '')
DESTINATION_PLACEHOLDER = u'{destination_folder}'

TRANSMISSION_RPC_URL = environ.get('TRANSMISSION_RPC_URL', u'http://192.168.0.2:9091/transmission/rpc')
TRANSMISSION_RPC_USERNAME = environ.get('TRANSMISSION_RPC_USERNAME', u'admin')
TRANSMISSION_RPC_PASSWORD = environ.get('TRANSMISSION_RPC_PASSWORD', u'admin')
# Where transmission saves completed torrents, as seen by transmission. Only differs from SOURCE_FOLDER when
# transmission and the filesystem worker mount the downloads volume at different paths.
TRANSMISSION_DOWNLOAD_DIR = environ.get('TRANSMISSION_DOWNLOAD_DIR', SOURCE_FOLDER)
# Torrents (and their data on the download volume) are removed after this many days of seeding.
TORRENT_RETENTION_DAYS = int(environ.get('TORRENT_RETENTION_DAYS', 90))

ALLOWED_HOSTS = ALLOWED_HOSTS + [environ.get('EXTRA_ALLOWED_HOST', u'192.168.0.101'), environ.get('EXTRA_ALLOWED_IP', u'127.0.0.1')]
DEBUG = env_bool('DEBUG', False)