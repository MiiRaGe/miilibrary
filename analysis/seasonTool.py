'''
Created on 1 fvr. 2014

@author: MiiRaGe
'''

import os,re
import logging

logger = logging.getLogger('NAS')

def analyse(path,fileToWriteTo):
    summary = dict()
    for serieFolder in os.listdir(path):
        logger.info("Entering :" + serieFolder)
        seasons = analyseSerie(os.path.join(path,serieFolder))
        summary[serieFolder] = seasons
    if os.path.exists(fileToWriteTo):
        os.remove(fileToWriteTo)
    fh = open(fileToWriteTo,"w")
    for serie in summary:
        fh.write(serie + " :\n")
        for seasons in summary[serie]:
            for season in seasons:
                fh.write("\t" + season +"\n")

    
def analyseSerie(path):
    seasons = []
    seasonsList = os.listdir(path)
    missingSeasons = []
    maxSeason = ''
    if seasonsList:
        seasonsList = sorted(seasonsList)
        maxSeason = re.search("(\d+)",seasonsList[-1:][0]).group(1)
        for i in range(1,int(maxSeason)+1):
            missingSeasons.append("Season "+str(i))
    for season in missingSeasons:
        if not os.path.exists(os.path.join(path,season)):
            seasons.append([season + " is missing"])
        else:
            s = []
            logger.info("\tEntering :" + season)
            episodes = analyseSeason(os.path.join(path,season))
            for episode in episodes:
                if episode.startswith(("Number")):
                    s.append(season + " : " + episode)
                else:
                    s.append( season + " :Missing Episode " + episode)
            
            seasons.append(s)
    seasons.append(["Number of seasons :" + maxSeason])
    return seasons

def analyseSeason(path):
    numbers = []
    for episode in os.listdir(path):
        logger.info("\t\tReading :"+ episode)
        numbers.append(int(re.search("[sS]\d*[eE]0*(\d+)",episode).group(1)))
    numbers.sort()
    max = numbers[len(numbers)-1]
    missings = []
    for missing in range(1,max+1):
        if numbers.count(missing) == 0:
            missings.append(missing)
    if missings == []:
        missings.append("Number of episodes :" + str(max))
    return map(str,missings)