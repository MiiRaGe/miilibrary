from django import *
from os import environ

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
DBBACKUP_STORAGE = environ.get('DBBACKUP_STORAGE', 'dbbackup.storage.filesystem_storage')
DBBACKUP_BACKUP_DIRECTORY = environ.get('DBBACKUP_BACKUP_DIRECTORY', '/tmp/backup/')

SENTRY_URL = environ.get('SENTRY_URL', '')
DESTINATION_PLACEHOLDER = u'{destination_folder}'