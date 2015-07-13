import sys
from django import *

#MiiNASLibrary configuration file

"""Configuration file"""
#This Folder is browsed recursively for .rar files and movie files (mkv,avi...)
SOURCE_FOLDER = ''

#This is the root of the media folder (destination)
DESTINATION_FOLDER = ''

#Architecture of outputFolder is as follow :
#outputFolder
#	#Movies
#		#All
#			#MOVIENAME (YEAR) [QUALITY*]
#				#MOVIENAME.(YEAR).[QUALITY*].EXTENSION
#				#.IMDB_ID_XXXXXXX
#		#... Index to come
#	#TVSeries
#		#SERIENAME
#			#Season X
#				#Episodes
#	#data (Folder containing media to be sorted)
#	#unsorted (Contains the files that were in conflict or that were unsortable for some reason)
#	#logs (circular logs)
#		#miinaslibrary.log.0
#		#		...
#		#miinaslibrary.log.5
#	#miinaslibrary.log (link to last log)
#	#TVStatistics.txt (contains informations about the sorted series, number of episodes/seasons, missing episodes/seasons)

"""[Unpacking]"""
#Is the script unpacking and moving from the source folder (can be deactivated to only sort what's in the data folder)
UNPACKING_ENABLED = True

#Minimum size to be considered as non sample (in MB)
MINIMUM_SIZE = 125

#Delete the empty folders in the source folder, useful when resorting the whole TVSeries output folder
SOURCE_CLEANUP = False

"""[Sorting]"""
#Contain custom rules for renaming
CUSTOM_RENAMING = {
    'dummy name US': 'name',
}

"""[OpenSubtitle]"""
OPENSUBTITLE_API_URL = "https://api.opensubtitles.org/xml-rpc"
OPENSUBTITLE_LOGIN = ''
OPENSUBTITLE_PASSWORD = ''


"""[RSS Link]"""
RSS_URL = 'http://www.torrentday.com/torrents/rss?download;l7;u=xxx;tp=xxx'
TORRENT_WATCHED_FOLDER = '/PATH/TO/WATCHED/FOLDER/'
RSS_FILTERS = [
    'the.peoples.couch.*720p'
]

"""[Django Databases]"""
DATABASES['default']['NAME'] = 'media'
DATABASES['default']['USER'] = 'MiiRaGe'
DATABASES['default']['PASSWORD'] = '1234'
DATABASES['default']['HOST'] = 'localhost'

#Set them equal to local_root if not using a nas
LOCAL_ROOT = '/mnt/smb_folder/'

#Those parameter will ssh log and link files remotely.
REMOTE_FILE_OPERATION_ENABLED = False
NAS_IP = ''
NAS_USERNAME = 'foo'
NAS_ROOT = '/share/MD0_DATA/'
MEDIA_RENDERER_RESCAN_URL = 'http://192.168.0.2:9000/rpc/rescan'