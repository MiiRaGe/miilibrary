import logging
import os

from django.conf import settings

from mii_common import tools
from mii_indexer.logic import Indexer
from mii_sorter.logic import Sorter
from mii_unpacker.logic import RecursiveUnrarer


logger = logging.getLogger(__name__)


class MiiNASLibrary:
    def __init__(self):
        # #### Folder Initialisation #####
        self.source_dir = None
        self.output_dir = None
        self.data_dir = None

        # #### Modules Initialisation #####
        self.recursive_unrarer = RecursiveUnrarer()
        self.sorter = Sorter()
        self.indexer = Indexer()

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
