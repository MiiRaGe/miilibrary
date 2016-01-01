import os
import re
import shutil
import subprocess

from pyreport import reporter
from django.conf import settings
from middleware.remote_execution import link, unrar
from mii_common import tools
from mii_sorter.models import insert_report

from mii_unpacker.models import Unpacked

if settings.REPORT_ENABLED:
    logger = reporter.Report()
else:   # pragma: no branch
    import logging
    logger = logging.getLogger(__name__)


class RecursiveUnrarer:
    def __init__(self):
        self.destination_dir = tools.make_dir(os.path.join(settings.DESTINATION_FOLDER, "data"))
        self.source_dir = settings.SOURCE_FOLDER
        self.level = 0
        self.removed = 0
        self.extracted = 0
        self.linked = 0
    
    def run(self):
        self.unrar_and_link()
        self.cleanup()
        self.print_statistic()

    def unrar_and_link(self):
        if settings.REPORT_ENABLED:
            logger.create_report()
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
        for data_file in os.listdir(current_directory):
            full_file_path = os.path.join(current_directory, data_file)
            if os.path.isfile(full_file_path):
                if data_file.endswith(".part01.rar"):
                    logger.debug("%sExtracting :%s" % (indent, data_file))
                    self.unrar(full_file_path, data_file)

                elif re.match(".*\.part[0-9]*\.rar$", data_file):
                    logger.debug("%sBypassing :%s" % (indent, data_file))

                elif data_file.endswith(".rar"):
                    logger.debug("%sExtracting :%s" % (indent, data_file))
                    self.unrar(full_file_path, data_file)

                elif re.match(".*\.(mkv|avi|mp4|mpg)$", data_file) and \
                                os.path.getsize(full_file_path) > settings.MINIMUM_SIZE * 1000000:
                    # Moving every movie type, cleanup later
                    if self.link_video(current_directory, data_file):
                        logger.debug("%sMoving :%s to the data folder..." % (indent, data_file))

            elif os.path.isdir(full_file_path) and full_file_path is not self.destination_dir:
                self.level += 1
                self.recursive_unrar_and_link(full_file_path)
                self.level -= 1

    def unrar(self, archive_file, file_name):
        if Unpacked.objects.filter(filename=file_name).exists():
            return
        logger.debug("Processing extraction...")

        try:
            output = unrar(archive_file, self.destination_dir)
            # TODO : Do something with execution_result.output.
            # TODO : Log in a table
            logger.debug("Extraction OK!")
            Unpacked.objects.create(filename=file_name)
            self.extracted += 1
        except subprocess.CalledProcessError as cpe:
            logger.error("Extraction failed code=%s, output=%s", cpe.returncode, cpe.output)
        return

    def cleanup(self):
        logger.info("-------------Clean-up data Folder-------------")
        self.removed = 0
        for media_file in os.listdir(self.destination_dir):
            # If it's not a movie media_file or if the size < MINIMUM_SIZE Mo (samples)
            logger.debug("Reading (cleanup):%s" % media_file)
            if not re.match(".*\.(mkv|avi|mp4|mpg)", media_file):
                logger.debug("Removing (Reason : not a movie):")
                os.remove(self.destination_dir + os.path.sep + media_file)
                self.removed += 1
            else:
                if os.path.getsize(self.destination_dir + os.path.sep + media_file) < settings.MINIMUM_SIZE * 1000000\
                        or 'sample' in media_file:
                    logger.debug("Removing (Reason : size < %sMo): %s" % (settings.MINIMUM_SIZE, media_file))
                    os.remove(self.destination_dir + os.path.sep + media_file)
                    self.removed += 1
                # if os.path.islink(os.path.join(self.destination_dir, media_file)):
                #     os.unlink(os.path.join(self.destination_dir, media_file))

    def link_video(self, source_path, file_to_link):
        source_file = os.path.join(source_path, file_to_link)
        destination_file = os.path.join(self.destination_dir, file_to_link)
        if Unpacked.objects.filter(filename=file_to_link).exists():
            logger.error("Not linking, same file exist (weight wise)")
            return False

        if os.path.exists(destination_file):
            if os.path.getsize(destination_file) < os.path.getsize(source_file):
                os.remove(destination_file)
                try:
                    link(source_file, destination_file)
                except AttributeError:
                    shutil.copy(source_file, destination_file)
                self.linked += 1
                Unpacked.objects.create(filename=file_to_link)
                return True
            else:
                logger.error("Not linking, same file exist (weight wise)")
                return False
        else:
            try:
                link(source_file, destination_file)
            except AttributeError:
                shutil.copy(source_file, destination_file)
            Unpacked.objects.create(filename=file_to_link)
            self.linked += 1
            return True

    def print_statistic(self):
        logger.info("-----------Summary-----------")
        logger.info("Extracted : %s" % self.extracted)
        logger.info("Linked : %s" % self.linked)
        logger.info("Removed : %s" % self.removed)
        if settings.REPORT_ENABLED:
            insert_report(logger.finalize_report(), report_type='unpacker')

