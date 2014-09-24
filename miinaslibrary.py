import logging
import os

import tools
import settings

from analysis import seasonTool as season_tool
from indexer import Indexer
from sorter import sorter
from unpacker import UnpackerMain


logger = logging.getLogger('NAS')


class MiiNASLibrary:
    def __init__(self):
        tools.init_log()
        # #### Folder Initialisation #####
        self.source_dir = settings.SOURCE_FOLDER
        self.output_dir = settings.DESTINATION_FOLDER
        self.movie_dir = os.path.join(self.output_dir, "Movies")
        self.data_dir = tools.make_dir(os.path.join(self.output_dir, "data"))

        # #### Modules Initialisation #####
        self.recursive_unrarer = UnpackerMain.RecursiveUnrarer(self.source_dir, self.data_dir)
        self.sorter = sorter.Sorter(self.output_dir)
        self.indexer = Indexer.Indexer(self.movie_dir)
        tools.print_rec(settings.DESTINATION_FOLDER)

    def run(self):
        tools.shift_log()

        logger.info("---MiiNASLibrary---")
        self.unpack()
        self.sort()
        logger.info("Analysis Module :")
        # st.analyse(os.path.join(destination_dir,'TVSeries'),os.path.join(destination_dir,'TVStatistics.txt'))
        self.index()

    def unpack(self):
        """
            Run the unpacker on source folder, put media in data folder

        """
        logger.info("Unpacking Module :")
        self.recursive_unrarer.unrar_and_link()
        self.recursive_unrarer.cleanup()
        if settings.SOURCE_CLEANUP:
            pass
            # Complete wiping of source folder
            # tools.cleanup_source(self.source_dir)
        self.recursive_unrarer.print_statistic()

    def sort(self):
        """
            Run the sorter on destination folder using the data folder

        """
        logger.info("Sorting Module :")
        self.sorter.sort()

    def index(self):
        """
            Run the indexing on destination folder using the movies/all folder

        """
        logger.info("Indexing Module :")
        self.indexer.index()