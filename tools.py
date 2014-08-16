import os
import logging
import datetime

import settings
from movieinfo import theMovieDBWrapper, opensubtitleWrapper


#Create the directory @param(path) and return the path after creation [Error safe]
def make_dir(path):
    #Avoid the raise of IOError exception by checking if the directory exists first
    try:
        os.makedirs(path)
    except Exception as e:
        logger.exception("Got an exception in make_dir, %s" % repr(e))
    return path


#Remove a file [Error safe]
def remove(path):
    try:
        os.remove(path)
    except Exception as e:
        logger.exception("Got an exception in remove, %s" % repr(e))

#Initialise Wrappers :
MovieDBWrapper = theMovieDBWrapper.TheMovieDBWrapper()
OpensubtitleWrapper = opensubtitleWrapper.OpensubtitleWrapper()

########### LOG #############
#Creating the log directory
output_dir = os.path.join(settings.DESTINATION_FOLDER, 'log')
try:
    os.makedirs(output_dir)
except OSError as e:
    pass



#Creating the logger named 'NAS' and configuring
logger = logging.getLogger('NAS')

#Where it's written to
hdlr = logging.FileHandler(os.path.join(output_dir, 'myNasLibrary.log.0'))
logger.addHandler(hdlr)

#How it's formated in the logs
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)

#Amount of information in the tool
logger.setLevel(logging.DEBUG)


#Shift the logs file in order to have different runs of the script (0->1,1->2) etc...    
def shift_log():
    #Removing the handler
    logger.removeHandler(hdlr) 
     
    #Timestamp for the logfile
    timestamp = datetime.datetime.now().strftime("%d-%m-%y.%H:%M")
    
    hdlr2 = logging.FileHandler(os.path.join(output_dir, 'myNasLibrary' + timestamp + '.log'))
    #Readding the handler
    logger.addHandler(hdlr2)
