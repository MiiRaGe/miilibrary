import logging
import os

import tools
import settings

from analysis import seasonTool as st
from indexer import Indexer
from sorter import Sorter
from unpacker import UnpackerMain


class MiiNASLibrary:
    def __init__(self):
        tools.init_log()
        ##### Folder Initialisation #####
        self.source_dir = settings.SOURCE_FOLDER
        self.output_dir = settings.DESTINATION_FOLDER
        self.movie_dir = os.path.join(self.output_dir, "Movies")
        self.data_dir = tools.make_dir(os.path.join(self.output_dir, "data"))

        ##### Modules Initialisation #####
        self.recursive_unrarer = UnpackerMain.RecursiveUnrarer(self.source_dir, self.data_dir)
        self.sorter = Sorter.Sorter(self.output_dir)
        self.indexer = Indexer.Indexer(self.movie_dir)

    def run(self):
        tools.shift_log()

        logger = logging.getLogger('NAS')
        logger.info("---MiiNASLibrary---")
        logger.info("Unpacking Module :")
        self.doUnpack()
        logger.info("Sorting Module :")
        self.doSort()
        logger.info("Analysis Module :")
        #st.analyse(os.path.join(destination_dir,'TVSeries'),os.path.join(destination_dir,'TVStatistics.txt'))
        logger.info("Indexing Module :")
        self.doIndex()

    def doIndex(self):
        self.indexer.index()

    def doSort(self):
        self.sorter.sort()

    def doUnpack(self):
        self.recursive_unrarer.unrar_and_link()
        self.recursive_unrarer.cleanup()
        if settings.SOURCE_CLEANUP:
            self.recursive_unrarer.cleanup_source(self.source_dir)
        self.recursive_unrarer.print_statistic()
