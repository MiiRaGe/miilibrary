'''
Created on 15 janv. 2014

@author: miistair
'''
import subprocess
from os import listdir
import re
import os
import shutil,logging
logger = logging.getLogger("NAS")

class RecursiveUnrarer :
    
    def __init__(self, source, dataDir):
        self.outputDir = dataDir
        self.alphabeticalDir = source
        self.level = 0
        
    def unrarAndMove(self):
        self.extracted = 0
        self.moved = 0
        self.recursiveUnrarAndMove(self.alphabeticalDir)
        
    def recursiveUnrarAndMove(self,path):
        indent = ""
        for i in range(0,self.level -1):
            indent += "\t"

        logger.debug(indent + "Entering :" + path + ":")
        indent += "\t"
        for dataFile in listdir(path):
            # First case dataFile type
            fullPath = os.path.join(path,dataFile)
            if os.path.isfile(fullPath):
                if dataFile.endswith(".part01.rar"): 
                    logger.debug(indent + "Extracting :" + dataFile)
                    self.unrar(fullPath)
                elif re.match(".*\.part[0-9]*\.rar$", dataFile):
                    logger.debug(indent +"Bypassing :" +dataFile)
                elif dataFile.endswith(".rar"):
                    logger.debug(indent +"Extracting :" + dataFile)
                    self.unrar(fullPath)
                elif (re.match(".*\.(mkv|avi|mp4|mpg)$",dataFile) and os.path.getsize(fullPath) > 125000000):
                    #Moving every movie type, cleanup later
                    logger.debug(indent +"Moving :" + dataFile + " to the data folder...")
                    self.moveVideo(path, dataFile)
            # Second Case directory type
            elif os.path.isdir(fullPath) and fullPath is not self.outputDir:
                self.level += 1
                self.recursiveUnrarAndMove(fullPath)
                self.level -= 1
             
    def unrar(self,archiveFile):
        if os.path.exists(archiveFile + "_extracted"):
            return
        os.chdir(self.outputDir)
        logger.debug("Processing extraction...")
        retval = subprocess.call('unrar e -y ' + archiveFile, shell=True)
        if (retval == 0 ):
            logger.debug("Extraction OK!")
            open(archiveFile + "_extracted", "w")
            self.extracted += 1
        else:
            logger.error("Extraction failed")
        return
         
    def cleanup(self):
        logger.info("-------------Clean-up data Folder-------------")
        self.removed = 0
        for mediaFile in os.listdir(self.outputDir):
            #If it's not a morvgblt??vie mediaFile or if the size < 100Mo (samples)
            logger.debug("Reading (cleanup):" + mediaFile)
            if not re.match(".*\.(mkv|avi|mp4|mpg)",mediaFile):
                logger.debug("Removing (Reason : not a movie):")
                os.remove(self.outputDir + os.path.sep + mediaFile)
                self.removed += 1
            else:
                if (os.path.getsize(self.outputDir + os.path.sep + mediaFile) < 125000000):
                    logger.debug("Removing (Reason : probably a sample since <125Mo): " + mediaFile)
                    os.remove(self.outputDir + os.path.sep + mediaFile)
                    self.removed += 1
                    
    def moveVideo(self,sourcePath,fileToMove):
        outputFile = self.outputDir + os.path.sep + fileToMove
        if os.path.exists(outputFile):
            if os.path.getsize(outputFile) != os.path.getsize(sourcePath + os.path.sep + fileToMove):
                os.remove(outputFile)
                os.rename(sourcePath + os.path.sep + fileToMove, outputFile)
                self.moved += 1
            else:
                logger.error("Not moving, same file exist (weight wise)")
        else :
            os.rename(sourcePath + os.path.sep + fileToMove, self.outputDir + os.path.sep + fileToMove)
            self.moved += 1
    
    def printStatistic(self):
        logger.info("-----------Summary-----------")
        logger.info("Extracted : " + str(self.extracted))
        logger.info("Moved : " + str(self.moved))
        logger.info("Removed : " + str(self.removed))
        logger.info("-----------------------------")
        
    def cleanupSource(self,source):
            logger.info("-------------Clean-up Source-------------")
            for mediaFile in os.listdir(source):
                #If it's not a movie mediaFile or if the size < 100Mo (samples)
                logger.info("Reading (cleanup):" + mediaFile)
                if os.path.isdir(os.path.join(source,mediaFile)):
                    if os.listdir(os.path.join(source,mediaFile)) == []:
                        shutil.rmtree(os.path.join(source,mediaFile))
                    else:
                        self.cleanupSource(os.path.join(source,mediaFile))
                        if os.listdir(os.path.join(source,mediaFile)) == []:
                            shutil.rmtree(os.path.join(source,mediaFile))
                    
    
