import logging

from collections import defaultdict

from mii_sorter.models import Episode


logger = logging.getLogger(__name__)


def analyse_series():
    series = defaultdict(lambda: defaultdict(list))
    for episode in Episode.objects.values('number', 'season__number', 'season__serie__name'):
        series[episode['season__serie__name']][int(episode['season__number'])].append(int(episode['number']))
    return get_series_report(series)


def get_series_report(series):
    report = defaultdict(lambda: defaultdict(list))
    for serie, seasons in series.items():
        for i in range(1, max(seasons.keys()) + 1):
            if i not in seasons.keys():
                report[serie][i].append('Season Missing')
            else:
                report[serie][i] = get_season_report(seasons[i])
                report[serie][-1] = report[serie].get(-1, 0) + 1
    return report


def get_season_report(episodes):
    season_report = []
    for i in range(1, max(episodes)):
        if i not in episodes:
            season_report.append('Episode %s missing' % i)
    return season_report
