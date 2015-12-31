import logging
import os
import re

from collections import defaultdict

from mii_sorter.models import Episode


logger = logging.getLogger(__name__)


def analyse_series():
    summary = defaultdict(lambda:defaultdict(list))
    for episode in Episode.objects.values('number', 'season__number', 'season__serie__name'):
        summary[episode['season__serie__name']][int(episode['season__number'])].append(int(episode['number']))
    print summary


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