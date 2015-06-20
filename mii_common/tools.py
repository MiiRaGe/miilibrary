import commands
import logging
import os
import shutil
import subprocess

from django.conf import settings
from movieinfo import the_movie_db_wrapper, opensubtitle_wrapper

logger = logging.getLogger(__name__)


#Create the directory @param(path) and return the path after creation [Error safe]
def make_dir(path):
    #Avoid the raise of IOError exception by checking if the directory exists first
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != 17:
            logger.warning('Exception in make_dir(%s): %s' % (e.filename, repr(e)))
    return path


#Remove a file [Error safe]
def remove(path):
    try:
        os.remove(path)
    except OSError as e:
        logger.warning("Exception in remove, %s" % repr(e))


def validate_settings():
    if settings.SOURCE_FOLDER == '':
        print "Error, settings.SOURCE_FOLDER can't be empty"
    if settings.DESTINATION_FOLDER == '':
        print "Error, settings.DESTINATION_FOLDER can't be empty"
    if not os.path.exists(settings.SOURCE_FOLDER):
        print "Error in settings.SOURCE_FOLDER, %s does not exist" % settings.SOURCE_FOLDER
    if not os.path.exists(settings.DESTINATION_FOLDER):
        print "Error in settings.DESTINATION_FOLDER, %s does not exist" % settings.DESTINATION_FOLDER
    if not isinstance(settings.MINIMUM_SIZE, float):
        print "settings.MINIMUM_SIZE have to be an int or float"
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
               isinstance(settings.MINIMUM_SIZE, float),
               settings.MINIMUM_SIZE >= 0,
               isinstance(settings.CUSTOM_RENAMING, dict),
               isinstance(settings.UNPACKING_ENABLED, bool),
               isinstance(settings.SOURCE_CLEANUP, bool)])


def getstatusoutput(cmd):
    """Return (status, output) of executing cmd in a shell."""
    return commands.getstatusoutput(cmd)


def delete_dir(path):
    """deletes the path entirely"""
    cmd = "rm -rf \"%s\"" % path
    output = getstatusoutput(cmd)
    if output[0]:
        raise RuntimeError(output[1])


def delete_file(path):
    """deletes the file entirely"""
    return_value = subprocess.call("rm \"%s\"" % path, shell=True)
    if return_value:
        raise RuntimeError("Rm failed for %s" % path)


def cleanup_rec(source):
    for media_file in os.listdir(source):
        if media_file == '.gitignore':
                    continue
        logger.info("\t\t * Removing: %s *" % media_file)
        if os.path.isdir(os.path.join(source, media_file)):
            if os.listdir(os.path.join(source, media_file)):
                cleanup_rec(os.path.join(source, media_file))
            try:
                shutil.rmtree(os.path.join(source, media_file))
            except:
                try:
                    os.remove(os.path.join(source, media_file))
                except:
                    pass
        else:
            os.remove(os.path.join(source, media_file))


def print_rec(path, indent=0):
    tabulation = ''
    for i in range(0, indent):
        tabulation += '\t'
    pos = -1
    if path.endswith('/'):
        pos = -2
    print '%s%s %s' % (tabulation, path.split('/')[pos], '(Dir):' if os.path.isdir(path) else '(File)')

    if os.path.isdir(path):
        for file in sorted(os.listdir(path)):
            print_rec(os.path.join(path, file), indent + 1)


def listdir_abs(parent):
    return [os.path.join(parent, child) for child in os.listdir(parent)]