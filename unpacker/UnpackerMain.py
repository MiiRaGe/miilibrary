import logging
import os
import re
import shutil
import subprocess
from os import listdir

import settings
import tools

try:
    raise WindowsError
except NameError:
    WindowsError = None
except Exception:
    pass

logger = logging.getLogger("NAS")


class RecursiveUnrarer:
    def __init__(self, source, data_dir):
        self.destination_dir = data_dir
        self.source_dir = source
        self.level = 0
        self.removed = 0
        self.extracted = 0
        self.linked = 0

    def unrar_and_link(self):
        logger.info("****************************************")
        logger.info("**********      Unpacker      **********")
        logger.info("****************************************")
        self.linked = 0
        self.extracted = 0
        self.recursive_unrar_and_link(self.source_dir)

    def recursive_unrar_and_link(self, current_directory):
        indent = ""
        for i in range(0, self.level - 1):
            indent += "\t"

        logger.debug("%sEntering : %s" % (indent, current_directory))
        indent += "\t"
        try:
            for data_file in listdir(current_directory):
                full_file_path = os.path.join(current_directory, data_file)
                if os.path.isfile(full_file_path):
                    if data_file.endswith(".part01.rar"):
                        logger.debug("%sExtracting :%s" % (indent, data_file))
                        self.unrar(full_file_path)

                    elif re.match(".*\.part[0-9]*\.rar$", data_file):
                        logger.debug("%sBypassing :%s" % (indent, data_file))

                    elif data_file.endswith(".rar"):
                        logger.debug("%sExtracting :%s" % (indent, data_file))
                        self.unrar(full_file_path)

                    elif re.match(".*\.(mkv|avi|mp4|mpg)$", data_file) and \
                                    os.path.getsize(full_file_path) > settings.MINIMUM_SIZE * 1000000:
                        #Moving every movie type, cleanup later
                        logger.debug("%sMoving :%s to the data folder..." % (indent, data_file))
                        self.link_video(current_directory, data_file)

                elif os.path.isdir(full_file_path) and full_file_path is not self.destination_dir:
                    self.level += 1
                    self.recursive_unrar_and_link(full_file_path)
                    self.level -= 1
        except WindowsError:
            logger.debug("%sDirectory empty :%s:" % (indent, current_directory))

    def unrar(self, archive_file):
        if os.path.exists(archive_file + "_extracted"):
            return
        logger.debug("Processing extraction...")

        stdout = open("%s/log/extractions/%s.extraction.LOG" % (settings.DESTINATION_FOLDER, archive_file.split('/')[-1]), "wb")
        return_value = subprocess.call('unrar e -y %s %s' % (archive_file, self.destination_dir), shell=True, stdout=stdout)
        if not return_value:
            logger.debug("Extraction OK!")
            open(archive_file + "_extracted", "w")
            self.extracted += 1
        else:
            logger.error("Extraction failed")
        return

    def cleanup(self):
        logger.info("-------------Clean-up data Folder-------------")
        self.removed = 0
        for media_file in os.listdir(self.destination_dir):
            #If it's not a movie media_file or if the size < MINIMUM_SIZE Mo (samples)
            logger.debug("Reading (cleanup):%s" % media_file)
            if not re.match(".*\.(mkv|avi|mp4|mpg)", media_file):
                logger.debug("Removing (Reason : not a movie):")
                os.remove(self.destination_dir + os.path.sep + media_file)
                self.removed += 1
            else:
                if os.path.getsize(self.destination_dir + os.path.sep + media_file) < settings.MINIMUM_SIZE * 1000000:
                    logger.debug("Removing (Reason : size < %sMo): %s" % (settings.MINIMUM_SIZE, media_file))
                    os.remove(self.destination_dir + os.path.sep + media_file)
                    self.removed += 1

    def link_video(self, source_path, file_to_link):
        source_file = source_path + os.path.sep + file_to_link
        destination_file = self.destination_dir + os.path.sep + file_to_link
        if os.path.exists(destination_file):
            if os.path.getsize(destination_file) != os.path.getsize(source_file):
                os.remove(destination_file)
                try:
                    os.link(source_file, destination_file)
                except AttributeError:
                    shutil.copy(source_file, destination_file)
                self.linked += 1
            else:
                logger.error("Not linking, same file exist (weight wise)")
        else:
            try:
                os.link(source_file, destination_file)
            except AttributeError:
                shutil.copy(source_file, destination_file)
            self.linked += 1

    def print_statistic(self):
        logger.info("-----------Summary-----------")
        logger.info("Extracted : %s" % self.extracted)
        logger.info("Linked : %s" % self.linked)
        logger.info("Removed : %s" % self.removed)

