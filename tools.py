import commands
import datetime
import logging
import os
import shutil
import subprocess
import sys

import settings
from movieinfo import theMovieDBWrapper, opensubtitleWrapper


#Create the directory @param(path) and return the path after creation [Error safe]
def make_dir(path):
    #Avoid the raise of IOError exception by checking if the directory exists first
    try:
        os.makedirs(path)
    except Exception, e:
        logger.exception("Got an exception in make_dir, %s" % repr(e))
    return path


#Remove a file [Error safe]
def remove(path):
    try:
        os.remove(path)
    except Exception, e:
        logger.exception("Got an exception in remove, %s" % repr(e))

#Initialise Wrappers :
MovieDBWrapper = theMovieDBWrapper.TheMovieDBWrapper()
OpensubtitleWrapper = opensubtitleWrapper.OpensubtitleWrapper()

########### LOG #############

handler = None
logger = logging.getLogger('NAS')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')


def init_log():
    #Creating the log directory
    log_dir = os.path.join(settings.DESTINATION_FOLDER, 'log')
    try:
        os.makedirs(log_dir)
    except OSError, e:
        pass

    try:
        os.makedirs('%s/extractions/' % log_dir)
    except OSError, e:
        pass

    timestamp = datetime.datetime.now().strftime("%d_%m_%y.%H-%M")
    handler = logging.FileHandler(os.path.join(log_dir, 'miiNasLibrary.%s.LOG' % timestamp))
    logger.addHandler(handler)

    handler.setFormatter(formatter)

    #Amount of information in the tool
    logger.setLevel(logging.DEBUG)


def remove_handler():
    #Removing the handler
    logger.removeHandler(handler)
    handler.close()


#Shift the logs file in order to have different runs of the script (0->1,1->2) etc...
def shift_log():
    remove_handler()

    #Timestamp for the logfile
    timestamp = datetime.datetime.now().strftime("%y_%m_%d.%H-%M")

    log_dir = os.path.join(settings.DESTINATION_FOLDER, 'log')
    handler2 = logging.FileHandler(os.path.join(log_dir, 'miiNasLibrary.%s.LOG' % timestamp))
    handler2.setFormatter(formatter)

    #Readding the handler
    logger.addHandler(handler2)


def validate_settings():
    if settings.SOURCE_FOLDER == '':
        print "Error, settings.SOURCE_FOLDER can't be empty"
    if settings.DESTINATION_FOLDER == '':
        print "Error, settings.DESTINATION_FOLDER can't be empty"
    if not os.path.exists(settings.SOURCE_FOLDER):
        print "Error in settings.SOURCE_FOLDER, %s does not exist" % settings.SOURCE_FOLDER
    if not os.path.exists(settings.DESTINATION_FOLDER):
        print "Error in settings.DESTINATION_FOLDER, %s does not exist" % settings.DESTINATION_FOLDER
    if not isinstance(settings.MINIMUM_SIZE, int):
        print "settings.MINIMUM_SIZE have to be an int"
    if not settings.MINIMUM_SIZE >= 0:
        print "settings.MINIMUM_SIZE have to positive, got: %s" % settings.MINIMUM_SIZE
    if not isinstance(settings.CUSTOM_RENAMING, dict):
        print "settings.CUSTOM_RENAMING have to be an dict"
    if not isinstance(settings.UNPACKING_ENABLED, bool):
        print "settings.UNPACKING_ENABLED have to be an bool"
    if not isinstance(settings.SOURCE_CLEANUP, bool):
        print "settings.SOURCE_CLEANUP have to be an bool"

    return all([not settings.SOURCE_FOLDER == '',
               not settings.DESTINATION_FOLDER == '',
               os.path.exists(settings.SOURCE_FOLDER),
               os.path.exists(settings.DESTINATION_FOLDER),
               isinstance(settings.MINIMUM_SIZE, int),
               settings.MINIMUM_SIZE >= 0,
               isinstance(settings.CUSTOM_RENAMING, dict),
               isinstance(settings.UNPACKING_ENABLED, bool),
               isinstance(settings.SOURCE_CLEANUP, bool)])


mswindows = (sys.platform == "win32")


def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    if not mswindows:
        return commands.getstatusoutput(cmd)
    pipe = os.popen('%s 2>&1' % cmd, 'r')
    text = pipe.read()
    sts = pipe.close()
    if sts is None:
        sts = 0
    if text[-1:] == '\n': text = text[:-1]
    return sts, text


def delete_dir(path):
    """deletes the path entirely"""
    if mswindows:
        cmd = "RMDIR \"%s\" /s /q" % path
    else:
        cmd = "rm -rf \"%s\"" % path
    output = getstatusoutput(cmd)
    if output[0]:
        raise RuntimeError(output[1])


def delete_file(path):
    """deletes the file entirely"""
    if mswindows:
        cmd = "ERASE \"%s\" /s /q" % path
        output = getstatusoutput(cmd)
        if output[0]:
            raise RuntimeError(output[1])
    else:
        return_value = subprocess.call("rm -rf \"%s\"" % path, shell=True)

def cleanup_rec(source):
    logger.info("-------------Clean-up Rec-------------")
    for media_file in os.listdir(source):
        logger.info("Reading (cleanup): %s" % media_file)
        if os.path.isdir(os.path.join(source, media_file)):
            if os.listdir(os.path.join(source, media_file)):
                cleanup_rec(os.path.join(source, media_file))
            shutil.rmtree(os.path.join(source, media_file))
        else:
            os.remove(os.path.join(source, media_file))
