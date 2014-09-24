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
OPENSUBTITLE_API_URL = "http://api.opensubtitles.org/xml-rpc"
OPENSUBTITLE_LOGIN = ''
OPENSUBTITLE_PASSWORD = ''

"""[Databases]"""
MONGO_HOST = 'localhost'
MONGO_PORT = 27017
MONGO_USER = 'MiiRaGe'
MONGO_PASSWORD = '1234'
MONGO_DB_NAME = 'miilibrary'

MYSQL_HOST = 'localhost'
MYSQL_PORT = 3306
MYSQL_USERNAME = 'MiiRaGe'
MYSQL_PASSWORD = '1234'
MYSQL_NAME = "media"
