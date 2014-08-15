from unpacker import UnpackerMain
from sorter import Sorter
from indexer import Indexer
from analysis import seasonTool as st
import Tool
import logging
import os
import settings
##### Folder Initialisation #####
source_dir = settings.SOURCE_FOLDER
output_dir = settings.UNPACKING_ENABLED
movie_dir = os.path.join(output_dir, "Movies")
data_dir = Tool.make_dir(os.path.join(output_dir, "data"))

##### Modules Initialisation #####
ru = UnpackerMain.RecursiveUnrarer(source_dir, data_dir)
s = Sorter.Sorter(output_dir)
indexer = Indexer.Indexer(movie_dir)


def miinaslibrary():
    
    Tool.shift_log()
    
    logger = logging.getLogger('NAS')
    logger.info("---MiiNASLibrary---")
    logger.info("Unpacking Module :")
    doUnpack(source_dir)
    logger.info("Sorting Module :")
    doSort()
    logger.info("Analysis Module :")
    #st.analyse(os.path.join(destination_dir,'TVSeries'),os.path.join(destination_dir,'TVStatistics.txt'))
    logger.info("Indexing Module :")
    doIndex()


def doIndex(): 
    indexer.index()


def doSort():
    s.sort()


def doUnpack(sourceFolder): 
    ru.unrar_and_link()
    ru.cleanup()
    if settings.SOURCE_CLEANUP:
        ru.cleanup_source(sourceFolder)
    ru.print_statistic()
