import logging
import os
import re
import settings
import shutil
import subprocess
from os import listdir

logger = logging.getLogger("NAS")


class RecursiveUnrarer:
    def __init__(self, source, data_dir):
        self.destination_dir = data_dir
        self.source_dir = source
        self.level = 0
        self.removed = 0
        self.extracted = 0
        self.moved = 0

    def unrar_and_link(self):
        self.moved = 0
        self.extracted = 0
        self.recursive_unrar_and_link(self.source_dir)

    def recursive_unrar_and_link(self, current_directory):
        indent = ""
        for i in range(0, self.level - 1):
            indent += "\t"

        logger.debug("%sEntering :%s:" % (indent, current_directory))
        indent += "\t"
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
                                os.path.getsize(full_file_path) > settings.MINIMUM_SIZE * 000000:
                    #Moving every movie type, cleanup later
                    logger.debug("%sMoving :%s to the data folder..." % (indent, data_file))
                    self.link_video(current_directory, data_file)

            elif os.path.isdir(full_file_path) and full_file_path is not self.destination_dir:
                self.level += 1
                self.recursive_unrar_and_link(full_file_path)
                self.level -= 1

    def unrar(self, archive_file):
        if os.path.exists(archive_file + "_extracted"):
            return
        os.chdir(self.destination_dir)
        logger.debug("Processing extraction...")
        return_value = subprocess.call('unrar e -y ' + archive_file, shell=True)
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
                if os.path.getsize(self.destination_dir + os.path.sep + media_file) < settings.MINIMUM_SIZE * 000000:
                    logger.debug("Removing (Reason : size < %sMo): %s" % (settings.MINIMUM_SIZE, media_file))
                    os.remove(self.destination_dir + os.path.sep + media_file)
                    self.removed += 1

    def link_video(self, source_path, file_to_link):
        source_file = source_path + os.path.sep + file_to_link
        destination_file = self.destination_dir + os.path.sep + file_to_link
        if os.path.exists(destination_file):
            if os.path.getsize(destination_file) != os.path.getsize(source_file):
                os.remove(destination_file)
                os.link(source_file, destination_file)
                self.moved += 1
            else:
                logger.error("Not linking, same file exist (weight wise)")
        else:
            os.link(source_file, destination_file)
            self.moved += 1

    def print_statistic(self):
        logger.info("-----------Summary-----------")
        logger.info("Extracted : %s" % self.extracted)
        logger.info("moved : %s" % self.moved)
        logger.info("Removed : %s" % self.removed)
        logger.info("-----------------------------")

    def cleanup_source(self, source):
        logger.info("-------------Clean-up Source-------------")
        for media_file in os.listdir(source):
            #If it's not a movie media_file or if the size < 100Mo (samples)
            logger.info("Reading (cleanup): %s" % media_file)
            if os.path.isdir(os.path.join(source, media_file)):
                if os.listdir(os.path.join(source, media_file)):
                    shutil.rmtree(os.path.join(source, media_file))
                else:
                    self.cleanup_source(os.path.join(source, media_file))
                    if os.listdir(os.path.join(source, media_file)):
                        shutil.rmtree(os.path.join(source, media_file))