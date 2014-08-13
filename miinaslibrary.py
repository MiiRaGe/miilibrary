from unpacker import UnpackerMain
from sorter import Sorter
from indexer import Indexer
from analysis import seasonTool as st
import Tool
import logging,os

##### Folder Initialisation #####
sourceDir = Tool.Configuration.get('Global','sourcefolder')
outputDir = Tool.Configuration.get('Global','outputfolder')
movieDir = os.path.join(outputDir,"Movies")
datadir = Tool.makeDir(os.path.join(outputDir,"data"))

##### Modules Initialisation #####
ru = UnpackerMain.RecursiveUnrarer(sourceDir,datadir)      
s = Sorter.Sorter(outputDir)
indexer= Indexer.Indexer(movieDir)

def miinaslibrary():
    
    Tool.shiftLog()
    
    logger = logging.getLogger('NAS')
    logger.info("---MiiNASLibrary---")
    logger.info("Unpacking Module :")
    doUnpack(sourceDir)
    logger.info("Sorting Module :")
    doSort()
    logger.info("Analysis Module :")
    #st.analyse(os.path.join(outputDir,'TVSeries'),os.path.join(outputDir,'TVStatistics.txt'))
    logger.info("Indexing Module :")
    doIndex()
    
def doIndex(): 
    indexer.index()

def doSort():
    s.sort()
    
def doUnpack(sourceFolder): 
    ru.unrarAndMove()
    ru.cleanup()
    if Tool.Configuration.getboolean('Global','sourceCleanup'):
        ru.cleanupSource(sourceFolder)
    ru.printStatistic()
