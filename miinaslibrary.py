import logging
import os

import settings

from mii_common import tools
from mii_indexer.indexer import Indexer
from mii_sorter.sorter import Sorter
from mii_unpacker.unpacker import RecursiveUnrarer


logger = logging.getLogger(__name__)


class MiiNASLibrary:
    def __init__(self):
        # #### Folder Initialisation #####
        self.source_dir = settings.SOURCE_FOLDER
        self.output_dir = settings.DESTINATION_FOLDER
        self.movie_dir = os.path.join(self.output_dir, "Movies")
        self.data_dir = tools.make_dir(os.path.join(self.output_dir, "data"))

        # #### Modules Initialisation #####
        self.recursive_unrarer = RecursiveUnrarer(self.source_dir, self.data_dir)
        self.sorter = Sorter(self.output_dir)
        self.indexer = Indexer(self.movie_dir)

    def run(self, sort_only=False, index_only=False):
        logger.info("---MiiNASLibrary---")
        if not sort_only and not index_only:
            self.unpack()
        if not index_only:
                self.sort()
        logger.info("Analysis Module :")
        # st.analyse(os.path.join(destination_dir,'TVSeries'),os.path.join(destination_dir,'TVStatistics.txt'))
        self.index()
        tools.print_rec(settings.DESTINATION_FOLDER)

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
