'''
Created on 18 janv. 2014

@author: miistair
'''

import os
import re
import sys
import logging
import Tool
import movieinfo.hashTool as ht

logger = logging.getLogger("NAS")

class Sorter:
    
    def __init__(self,mediaDir):
        self.mediaDir = mediaDir
        self.dataDir = os.path.join(mediaDir,"data")
        self.serieDir = os.path.join(mediaDir,"TVSeries")
        self.movieDir = os.path.join(mediaDir, "Movies")
        self.unsortedDir = os.path.join(mediaDir,"unsorted")
        self.alphabeticalMovieDir = os.path.join(self.movieDir, "All")
        Tool.makeDir(self.serieDir)
        Tool.makeDir(self.movieDir)
        Tool.makeDir(self.alphabeticalMovieDir)
        Tool.makeDir(self.unsortedDir)
    
    def createHashList(self,media):
        filePath = os.path.join(self.dataDir,media)
        moviehash = str(ht.hashFile(filePath))
        self.map[moviehash] = media
        self.hashArray.append(moviehash)

    def sort(self):
        logger.info("Login in the wrapper")
        Tool.OpensubtitleWrapper.logIn(True,10)
        logger.info("Beginning Sorting")
        self.hashArray = []
        self.map = dict()
        for media in os.listdir(self.dataDir):
            self.createHashList(media)
        
        for moviehash in self.hashArray:
            filename = self.map.get(moviehash)
            result = Tool.OpensubtitleWrapper.getSubtitles(moviehash, self.getSize(os.path.join(self.dataDir,filename)), "")
            isSorted = False
            if result:
                logger.info ("Got Result from opensubtitle for " + filename)
                logger.debug(result)
                if type(result) == list:
                    result = self.getBestMatch(result,filename)
                if result:
                    isSorted = self.sortOpenSubtitleInfo(result)
            else:
                result = Tool.OpensubtitleWrapper.getMovieNames2([moviehash,])
                if result:
                    logger.info(result)
                    result = result.get(moviehash)
                    if type(result) == list:
                        result = self.getBestMatch(result,filename)
                    if result:
                        isSorted = self.sortOpenSubtitleInfo(result)
                
            if not isSorted:
                if self.isSerie(self.map.get(moviehash)):
                    self.sortTVSerie(filename)
                    logger.info("Sorted the TV Serie :" + filename)
                else: 
                    logger.info("Probably a Movie? " + filename)
                    self.sortMovieFromName(filename)

    def isSerie(self,name):
        return re.match(".*[sS]\d\d[Ee]\d\d.*",name)
    
    def getBestMatch(self,resultList,filename):
        for result in resultList:
            if self.compare(filename,result):
                logger.info("Comparison returned true, moving on")
                return result
            else:
                logger.info("Comparison returned false, inconsistencies exist")
            
        return None
        
    def sortOpenSubtitleInfo(self,result):
        filename = self.map.get(result.get("MovieHash"))
        if result.get("MovieKind")=='movie':
            return self.createDirAndMoveMovie(result.get("MovieName"), result.get("MovieYear"), result.get("IDMovieImdb"), filename )
        else:
            parsing = re.match('"(.*)"(.*)',result.get("MovieName"))
            serieName = ""
            serieTitle = ""
            if parsing:
                serieName = parsing.group(1).strip()
                serieTitle = parsing.group(2).strip()
            else:
                serieName = result.get("MovieName")
                
            if result.get("SeriesSeason") == '0' or result.get("SeriesEpisode") == '0':
                self.serieRegEx = re.compile('[sS]0*(\d+)[eE](\d\d)')
                matched = self.serieRegEx.search(result.get('SubFileName'))
                if matched:
                    result["SeriesSeason"] = matched.group(1)
                    result["SeriesEpisode"] = matched.group(2)
            return self.createDirAndMoveSerie(serieName, result.get("SeriesSeason"),result.get("SeriesEpisode"), serieTitle, filename)
    
    def createDirAndMoveSerie(self,serieName,serieSeason, serieEpisodeNumber,serieTitle, filename):
            serieName = self.applyCustomRenaming(serieName)
            serieName = self.format(serieName)
            serieTitle = self.format(serieTitle)
            extension = filename[-4:]
            if len(serieEpisodeNumber) < 2 :
                serieEpisodeNumber = '0' + serieEpisodeNumber
                
            serieSeasonNumber = serieSeason
            if len(serieSeason) < 2 :
                serieSeasonNumber = '0' + serieSeason
            
            newFilename = serieName + "." + "S" + serieSeasonNumber + "E" + serieEpisodeNumber + "." +serieTitle + "."
            quality = self.getQuality(filename)
            if quality:
                newFilename += " ["+ quality + "]"
            newFilename += extension
            newFilename = re.sub(" +",".",newFilename)
            newFilename = re.sub("\.+",".",newFilename)
            resultDir = Tool.makeDir(os.path.join(self.serieDir,serieName))
            episodeDir = Tool.makeDir(os.path.join(resultDir + os.path.sep +"Season "+ serieSeason))
            try:
                
                existingEpisode = self.getEpisode(episodeDir, serieName, serieEpisodeNumber)
                if existingEpisode:
                    if os.path.getsize(os.path.join(episodeDir, existingEpisode)) >= os.path.getsize(os.path.join(self.dataDir,filename)):
                        self.moveToUnsorted(self.dataDir, filename)
                        logger.info("Moving the source to unsorted, episode already exists :" + existingEpisode)
                    else:
                        self.moveToUnsorted(episodeDir, existingEpisode)   
                        logger.info("Moving destination to unsorted (because bigger = better): " + newFilename)
                        os.rename(os.path.join(self.dataDir,filename), os.path.join(episodeDir,newFilename))
                    return True
                else:
                    logger.info("Moving the episode to the correct folder..."  + newFilename)
                    os.rename(os.path.join(self.dataDir,filename), os.path.join(episodeDir, newFilename))
                    return True
            except (WindowsError, OSError):
                logger.error(("Can't move "+os.path.join(self.dataDir,filename)))
                logger.error(sys.exc_info()[1])
                return False
    
    def sortTVSerie(self,media):
        newMedia = self.renameSerie(media)
        self.serieRegEx = re.compile('\A(.*)[sS]0*(\d+)[eE](\d\d).*\Z')
        result = self.serieRegEx.match(newMedia)
        if result:
            serieName = self.format(result.group(1))
            seasonnumber = result.group(2)
            episodeNumber = result.group(3)
            self.createDirAndMoveSerie(serieName,seasonnumber, episodeNumber,"", media)
    
    def applyCustomRenaming(self,seriename):
        lowerSeriename = seriename.lower()
        logger.info("Custom renamming :" + seriename)
        for item in Tool.Configuration.items('Sorting'):
            logger.debug("Applygin filter :" + item[0] + " -> " + item[1])
            result = re.sub(item[0],item[1],lowerSeriename)
            if not (result == lowerSeriename):
                logger.debug("Renamed :" + lowerSeriename + " to " + result)
                return result
        return seriename

    def sortMovieFromName(self,filename):
        filename
        info = self.getInfo(filename)
        if info is None:
            return False
        name = info.get("title")
        year = info.get("year")
        logger.info("Name/Year found from filename : Name = <"+ name  + ">" + " Year = <" + year + ">")
        result = Tool.MovieDBWrapper.getMovieName(name,year)
        logger.debug("Result from tmdb:" + str(result))
        if result:
            result = result[0]
            movieid = str(result.get("id"))
            logger.debug("Found Id : " + movieid )
            imdbid = Tool.MovieDBWrapper.getMovieIMDBID(movieid)
            if imdbid:
                imdbid = imdbid.get("imdb_id")
                self.createDirAndMoveMovie(result.get("title"),year, imdbid, filename)
                return True
        self.moveToUnsorted(self.dataDir, filename)
        return False
     
    def moveToUnsorted(self,filedir,filename):
        try:
            if os.path.exists(os.path.join(self.unsortedDir,filename)):
                os.remove(os.path.join(self.unsortedDir,filename))
            os.rename(os.path.join(filedir,filename), os.path.join(self.unsortedDir,filename))
        except (WindowsError, OSError):
            logger.error("Can't create "+ filename)
            logger.error(sys.exc_info()[1])
        
    def createDirAndMoveMovie(self,movieName,year,imdbid,filename):
        movieName = re.sub("[\*\:]","-",movieName) #Because Wall-e was WALL*E for some reason...and : isn't supported on winos...
        customMovieDir =  movieName + " (" + year + ")"
        quality =  self.getQuality(filename)
        if quality:
            customMovieDir += " [" + quality + "]"
        try:
            createdMovieDir = Tool.makeDir(os.path.join(self.alphabeticalMovieDir,customMovieDir))
            if imdbid:
                open(os.path.join(createdMovieDir,".IMDB_ID_"+imdbid), "w")
            newName = re.sub(".*(\.[a-zA-Z0-9]*)$", re.sub(" ",".",customMovieDir) + "\g<1>", filename)
            logger.info("Moving " + filename + ", with new name " + newName)
            os.rename(os.path.join(self.dataDir,filename),os.path.join(createdMovieDir,newName))
            return True
        except (WindowsError, OSError):
            logger.error("Can't create "+ customMovieDir)
            logger.error("Probably because windows naming convention sucks, skipping...")
            logger.error(sys.exc_info()[1])
            return False
        
    def getInfo(self,name):
        regexRes = re.match("(.*)(20[01][0-9]|19[5-9][0-9]).*",name)
        if regexRes:
            title = re.sub("[!\"$%&\*()_=';\-/,}\.{~@:?>< \t\n\r\f\v]"," ",regexRes.group(1))
            title = re.sub("  ", " ",title).strip()
            result = dict({"title":title,"year":regexRes.group(2)})
            return result
        return None
    
    def getSize(self,fileName):
        return str(os.path.getsize(os.path.join(self.dataDir,fileName)))
    
    def getQuality(self,name):
        quality = []
        regexRes = re.search("(720p|1080p)",name)
        if regexRes:
            quality.append(regexRes.group(1))
            
        if re.search("[aA][cC]3",name):
            quality.append("AC3")
            
        if re.search("DTS",name):
            quality.append("DTS")
            
        if re.search("([bB][lL][uU]-*[rR][aA][yY]|[bB][rR][Rr][iI][Pp])",name):
            quality.append("BluRay")
            
        if re.search("[wW][eE][bB]-*[RrdD][iIlL][pP]?",name):
            quality.append("WebRIP")
            
        return ','.join(quality)
    
    def getEpisode(self,episodeDir,serieName,number):
        for episode in os.listdir(episodeDir):
            if (re.search("[Ss]\d+[eE]" + number, episode )) :
                logger.info("Same episode found (" + serieName + " e" + number +") : "  + episode)
                return episode
        return None
    
    def format(self,serieName):
        serieName = re.sub("[!\"$%&\*()_=';\-/,}\.{~@:?>< \t\n\r\f\v]",".",serieName)
        serieName = re.sub("\.+",".",serieName)
        serieNameToken = serieName.split(".")
        return str.strip(' '.join(map(str.capitalize,serieNameToken)))
        
    def renameSerie(self,fileName):
        newMedia = re.sub("[!\"$%&\*()_=';\-/,}\.{~@:?>< \t\n\r\f\v]",".",fileName)
        newMedia = re.sub("\.\.",".",newMedia)
        if (re.sub("[^\d]([0-3]?\d)x(\d{1,2})[^\d]","S\g<1>E\g<2>",newMedia) is not newMedia):
            newMedia = re.sub("([0-3]?\d)x(\d{1,2})","S\g<1>E\g<2>",newMedia)
        return newMedia
    
    def compare(self,filename, result):
        logger.info("Comparing Opensubtitle result with filename for safety")
        if self.isSerie(filename):
            #Movie type consistency issue
            if result.get("MovieKind") == "movie":
                logger.info("Type Inconsistent : " + result.get("MovieKind") + " expected Tv Series/Episode")
                return False
            matchingPattern = re.search("[sS]0*(\d+)[eE]0*(\d+)",filename)
            if not ( result.get("SeriesSeason") == matchingPattern.group(1)) or not(result.get("SeriesEpisode") == matchingPattern.group(2)):
                logger.info("SXXEXX inconsistent : S" + result.get("SeriesSeason") + "E" + result.get("SeriesEpisode") + ", expected : S" + matchingPattern.group(1) + "E" + matchingPattern.group(2))
                return False
            #Otherwise it should be safe
            return True
        #Other case it's a movie
        if not (result.get("MovieKind") == "movie"):
            logger.info("Type Inconsistent : " + result.get("MovieKind") + " expected movie")
            return False
        #Year pattern result
        yearMatching = re.search("(20[01][0-9]|19[5-9][0-9])",filename)
        if yearMatching and not(yearMatching.group(1) == result.get("MovieYear")):
            logger.info("Year Inconsistent : " + result.get("MovieYear") + " expected year : " + yearMatching.group(1))
            return False
        
        #Otherwise it should be ok
        return True
                

