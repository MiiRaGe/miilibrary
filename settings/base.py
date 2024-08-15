# Import the configuration settings file - REPLACE projectname with your project
config_module = __import__('settings.django', globals(), locals(), 'django')

# Load the config settings properties into the local scope.
for setting in dir(config_module):
    if setting == setting.upper():
        locals()[setting] = getattr(config_module, setting)

from settings.django import DATABASES, CACHES
from os import environ
from settings.base import ALLOWED_HOSTS

#MiiNASLibrary configuration file

"""Configuration file"""
#This Folder is browsed recursively for .rar files and movie files (mkv,avi...)
SOURCE_FOLDER = environ.get('SOURCE_FOLDER', '')

#This is the root of the media folder (destination)
DESTINATION_FOLDER = environ.get('DESTINATION_FOLDER', '')

"""[Unpacking]"""
#Is the script unpacking and moving from the source folder (can be deactivated to only sort what's in the data folder)
UNPACKING_ENABLED = True

#Minimum size to be considered as non sample (in MB)
MINIMUM_SIZE = 125

#Delete the empty folders in the source folder, useful when resorting the whole TVSeries output folder
SOURCE_CLEANUP = False

"""[Sorting]"""
#Contain custom rules for renaming
# TODO: Move to DB regex.
CUSTOM_RENAMING = {
    'dummy name US': 'name',
}

"""[OpenSubtitle]"""
OPENSUBTITLE_API_URL = environ.get('OPENSUBTITLE_API_URL', "https://api.opensubtitles.org/xml-rpc")
OPENSUBTITLE_LOGIN = environ.get('OPENSUBTITLE_LOGIN', '')
OPENSUBTITLE_PASSWORD = environ.get('OPENSUBTITLE_PASSWORD', '')


"""[RSS Link]"""
RSS_URL = environ.get('RSS_URL', 'http://www.torrentday.com/torrents/rss?download;l7;u=xxx;tp=xxx')
TORRENT_WATCHED_FOLDER = environ.get('TORRENT_WATCHED_FOLDER', '/PATH/TO/WATCHED/FOLDER/')
# TODO: Move to DB.
RSS_FILTERS = [
    'the.peoples.couch.*720p'
]

"""[Django Databases]"""
DATABASES['default']['NAME'] = environ.get('DB_NAME', 'media')
DATABASES['default']['USER'] = environ.get('DB_USER', 'MiiRaGe')
DATABASES['default']['PASSWORD'] = environ.get('DB_PASSWORD', '1234')
DATABASES['default']['HOST'] = environ.get('DB_HOST', 'localhost')
DATABASES['default']['ENGINE'] = environ.get('DB_ENGINE', 'django.db.backends.sqlite3')

"""[Django Caches]"""
CACHES['default']['LOCATION'] = environ.get('CACHE_LOCATION', '127.0.0.1:6379')

"""[Django Secrets]"""
SECRET_KEY = environ.get('SECRET_KEY', '+^(g2=uuez(s1qgpmznc&amp;zx4win6o36*9d$7l=5!)tf77*110c')

"""[Django Origins]"""
CSRF_TRUSTED_ORIGINS = [u'https://' + environ.get('EXTRA_ALLOWED_HOST', u'localhost'), u'http://' + environ.get('EXTRA_ALLOWED_IP', u'127.0.0.1') ]

"""Celery Broker"""
BROKER_URL = environ.get('BROKER_URL', 'amqp://guest:**@localhost:5672//')
CELERY_BROKER_URL = BROKER_URL

#Set them equal to SOURCE_FOLDER if not using a remote storage.
# Some operation on the file are done remotely through SSH, so you need to provide the mapping between the mounted
# folder on the server, and the physical folder on the remote storage.
LOCAL_ROOT = environ.get('LOCAL_ROOT', '/mnt/smb_folder/')

#Those parameter will ssh log and link files remotely.
REMOTE_FILE_OPERATION_ENABLED = bool(environ.get('REMOTE_FILE_OPERATION_ENABLED', False))
NAS_IP = environ.get('NAS_IP', '')
NAS_USERNAME = environ.get('NAS_USERNAME', 'foo')
NAS_PASSWORD = environ.get('NAS_PASSWORD', 'bar')
NAS_ROOT = environ.get('NAS_ROOT', '/share/MD0_DATA/')
REMOTE_UNRAR_PATH = environ.get('NAS_UNRAR_PATH', u"/usr/local/sbin/unrar")

#Indexer
# This is enabling dumping the index data in a json file at the root of the MoviesSeries folder for another programm to index
DUMP_INDEX_JSON_FILE_NAME = environ.get('DUMP_INDEX_JSON_FILE_NAME', 'data.json')

REPORT_ENABLED = bool(environ.get('REPORT_ENABLED', True))

# Django-dbbackup settings
DBBACKUP_STORAGE = environ.get('DBBACKUP_STORAGE', 'django.core.files.storage.FileSystemStorage')
DBBACKUP_STORAGE_OPTIONS = {'location': environ.get('DBBACKUP_BACKUP_DIRECTORY', '/tmp/backup/')}

SENTRY_URL = environ.get('SENTRY_URL', '')
DESTINATION_PLACEHOLDER = u'{destination_folder}'

TRANSMISSION_RPC_URL = environ.get('TRANSMISSION_RPC_URL', u'http://192.168.0.2:9091/transmission/rpc')
TRANSMISSION_RPC_USERNAME = environ.get('TRANSMISSION_RPC_USERNAME', u'admin')
TRANSMISSION_RPC_PASSWORD = environ.get('TRANSMISSION_RPC_PASSWORD', u'admin')

ALLOWED_HOSTS = ALLOWED_HOSTS + [environ.get('EXTRA_ALLOWED_HOST', u'192.168.0.101'), environ.get('EXTRA_ALLOWED_IP', u'127.0.0.1')]
JSON_RPC_USERNAME = environ.get('JSON_RPC_USERNAME', 'kodi')
JSON_RPC_PASSWORD = environ.get('JSON_RPC_PASSWORD', 'kodi')
DEBUG = bool(environ.get('DEBUG', False))