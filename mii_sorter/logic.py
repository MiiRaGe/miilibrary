import logging
import os
import re
from time import sleep

from pyreport.reporter import Report
from middleware.remote_execution import symlink, remove_dir
from django.conf import settings
from middleware import mii_cache_wrapper
from mii_common import tools
from mii_sorter.models import WhatsNew, get_serie_episode, insert_serie_episode, get_movie, insert_movie, insert_report
from movieinfo import hash_tool as ht

logger = logging.getLogger(__name__)

if settings.REPORT_ENABLED:
    logger = Report()


class Sorter:
    mii_tmdb = mii_cache_wrapper.MiiTheMovieDB()
    mii_osdb = mii_cache_wrapper.MiiOpenSubtitleDB()

    def __init__(self):
        if settings.REPORT_ENABLED:
            logger.create_report()
        self.hash_array = []
        self.map = {}
        self.media_dir = settings.DESTINATION_FOLDER
        self.new_dir = os.path.join(self.media_dir, 'New')
        self.data_dir = os.path.join(self.media_dir, 'data')
        self.serie_dir = os.path.join(self.media_dir, 'TVSeries')
        self.movie_dir = os.path.join(self.media_dir, 'Movies')
        self.unsorted_dir = os.path.join(self.media_dir, 'unsorted')
        self.alphabetical_movie_dir = os.path.join(self.movie_dir, 'All')
        self.serie_regex = re.compile('[sS]0*(\d+)[eE](\d\d)')
        tools.make_dir(self.serie_dir)
        tools.make_dir(self.movie_dir)
        tools.make_dir(self.alphabetical_movie_dir)
        tools.make_dir(self.unsorted_dir)
        if os.path.exists(self.new_dir):
            remove_dir(self.new_dir)
        tools.make_dir(self.new_dir)

    def create_hash_list(self, media):
        file_path = os.path.join(self.data_dir, media)
        movie_hash = str(ht.hash_file(file_path))
        self.map[movie_hash] = media
        self.hash_array.append(movie_hash)
        self.hash_array = list(set(self.hash_array))

    def sort(self):
        logger.info(u'****************************************')
        logger.info(u'**********       Sorter       **********')
        logger.info(u'****************************************')
        # TODO optimize sorting
        self.map = {}
        self.hash_array = []
        for media in os.listdir(self.data_dir):
            self.create_hash_list(media)

        for movie_hash in sorted(self.hash_array):
            file_name = self.map.get(movie_hash).decode('utf-8')
            logger.info(u'------ %s ------' % file_name)
            result = self.mii_osdb.get_subtitles(movie_hash,
                                                 str(get_size(os.path.join(self.data_dir, file_name))))
            is_sorted = False
            if result:
                logger.info(u'Got Result from opensubtitle for %s' % file_name)
                if isinstance(result, list):
                    result = get_best_match(result, file_name)
                if result:
                    try:
                        is_sorted = self.sort_open_subtitle_info(result)
                    except Exception as e:
                        logger.exception(u'Error when sorting open_subtitle_info: %s, %s' % (file_name, repr(e)))
            else:
                result = self.mii_osdb.get_movie_name(movie_hash, number='2')
                if result:
                    logger.info(result)
                    result = result.get(movie_hash)
                    if type(result) == list:
                        result = get_best_match(result, file_name)
                    if result:
                        is_sorted = self.sort_open_subtitle_info(result)

            if not is_sorted:
                if is_serie(self.map.get(movie_hash)):
                    self.sort_tv_serie(file_name)
                    logger.info(u'Sorted the TV Serie : %s' % file_name)
                else:
                    logger.info(u'Looks like a movie')
                    self.sort_movie_from_name(file_name)

        self.update_new()
        if settings.REPORT_ENABLED:
            insert_report(logger.finalize_report(), report_type='sorting')

    def update_new(self):
        self.new_dir = tools.make_dir(self.new_dir)
        for whatsnew in WhatsNew.objects.all().order_by('-date')[:60]:
            if not os.path.exists(whatsnew.path):
                continue
            dir = tools.make_dirs(os.path.join(self.new_dir, whatsnew.get_displayable_date()))
            if os.path.isdir(whatsnew.path):
                logger.debug(u'Trying to link directory %s to %s' % (whatsnew.path, whatsnew.name))
                symlink(whatsnew.path, os.path.join(dir, whatsnew.name))
            else:
                logger.debug(u'Trying to link file %s to %s' % (whatsnew.path, whatsnew.name))
                symlink(whatsnew.path, os.path.join(dir, whatsnew.path.split('/')[-1]))

    def sort_open_subtitle_info(self, result):
        file_name = self.map.get(result.get('MovieHash'))
        if result.get('MovieKind') == 'movie':
            return self.create_dir_and_move_movie(result.get('MovieName'),
                                                  result.get('MovieYear'),
                                                  result.get('IDMovieImdb'),
                                                  file_name)
        else:
            parsing = re.match('"(.*)"(.*)', result.get('MovieName'))
            serie_title = ""
            if parsing:
                serie_name = parsing.group(1).strip()
                serie_title = parsing.group(2).strip()
            else:
                serie_name = result.get('MovieName')

            if result.get('SeriesSeason') == '0' or result.get('SeriesEpisode') == '0':
                matched = self.serie_regex.search(result.get('SubFileName'))
                if matched:
                    result['SeriesSeason'] = matched.group(1)
                    result['SeriesEpisode'] = matched.group(2)
            return self.create_dir_and_move_serie(serie_name,
                                                  result.get('SeriesSeason'),
                                                  result.get('SeriesEpisode'),
                                                  serie_title,
                                                  file_name)

    def create_dir_and_move_serie(self, name, season, episode_number, title, file_name):
        name = format_serie_name(apply_custom_renaming(name))
        title = format_serie_name(title)
        extension = file_name[-4:]
        if len(episode_number) < 2:
            episode_number = '0' + episode_number

        serie_season_number = season
        if len(season) < 2:
            serie_season_number = '0' + season

        new_file_name = '%s.S%sE%s.%s.' % (name, serie_season_number, episode_number, title)
        quality = get_quality(file_name)
        if quality:
            new_file_name += ' [%s]' % quality
        new_file_name += extension
        new_file_name = re.sub('[\s\.]+', '.', new_file_name)
        result_dir = tools.make_dir(os.path.join(self.serie_dir, name))
        season_dir = tools.make_dir(os.path.join(u'%s/Season %s' % (result_dir, season)))

        file_path = os.path.join(self.data_dir, file_name)
        try:
            exists, serie = get_serie_episode(name, int(season), int(episode_number))

            if exists and os.path.exists(serie.abs_file_path):
                if serie.file_size > os.path.getsize(file_path):
                    self.move_to_unsorted(file_path)
                    logger.info(u'Moving the source to unsorted, episode already exists :%s' % serie.abs_file_path)
                    return False
                elif serie.file_size == os.path.getsize(file_path):
                    os.remove(file_path)
                    logger.info(u'Removed the source, episode already exists and same size:%s' % serie.abs_file_path)
                    return False
                else:
                    self.move_to_unsorted(serie.abs_file_path)
                    logger.info(u'Moving destination to unsorted (because bigger = better): %s' % new_file_name)
                    os.rename(file_path, os.path.join(season_dir, new_file_name))
                    serie.file_path = os.path.join(season_dir, new_file_name)
                    serie.file_size = os.path.getsize(os.path.join(season_dir, new_file_name))
                    serie.save()
                return True
            else:
                if not exists:
                    insert_serie_episode(name,
                                         season,
                                         episode_number,
                                         os.path.join(season_dir, new_file_name),
                                         os.path.getsize(file_path))
                    logger.info(u'Created Serie object %s,S%sE%s' % (name, season, episode_number))
                else:
                    serie.file_path = os.path.join(season_dir, new_file_name)
                    serie.save()
                logger.info(u'Moving the episode to the correct folder...%s' % new_file_name)
                os.rename(file_path, os.path.join(season_dir, new_file_name))
                return True
        except OSError:
            logger.error(u'Can\'t move %s' % file_path)
            return False

    def sort_tv_serie(self, media):
        new_media = rename_serie(media)
        self.serie_regex = re.compile('\A(.*)[sS]0*(\d+)[eE](\d\d).*\Z')
        result = self.serie_regex.match(new_media)
        if result:
            serie_name = format_serie_name(result.group(1))
            season_number = result.group(2)
            episode_number = result.group(3)
            self.create_dir_and_move_serie(serie_name, season_number, episode_number, "", media)

    def sort_movie_from_name(self, file_name):
        info = get_info(file_name)
        if info is None:
            return False
        name = info.get('title')
        year = info.get('year')
        logger.info(u'Name/Year found from file_name : Name = <%s>, Year = <%s>' % (name, year))
        result = self.mii_tmdb.get_movie_name(name, year)
        logger.debug(u'Result from tmdb: %s' % result)
        if not result or not result.get('results'):
            logger.debug(u'Trying without the year')
            result = self.mii_tmdb.get_movie_name(name)
            logger.debug(u'Result from tmdb: %s' % result)
        try:
            if result and result.get('results'):
                result = result.get('results')[0]
                movie_id = str(result.get('id'))
                logger.debug(u'Matching result: %s' % result)
                matching_year = result.get('release_date', '1900-01-01')
                matched = re.match('(?:\d{4})', matching_year)
                if matched:
                    if not year:
                        year = matched.group(0)
                    else:
                        if year != matched.group(0):
                            logger.error(u'Year not matching for %s, Got %s expected %s' % (file_name,
                                                                                           matched.group(0),
                                                                                           year))
                        else:
                            logger.info(u'Year matched for %s' % file_name)
                percent = letter_coverage(name, result['title'])
                if percent > 65.0:
                    logger.info(u'Title matched %s, %s at (%s%%)' % (name, result['title'], percent))
                else:
                    raise Exception('Title did not match %s, %s with (%s%%)' % (name, result['title'], percent))

                imdb_id = self.mii_tmdb.get_movie_imdb_id(movie_id)
                logger.debug(u'Matching (id/imdb)  %s/%s' % (movie_id, imdb_id))
                if imdb_id:
                    imdb_id = imdb_id.get('imdb_id')
                    self.create_dir_and_move_movie(result['title'], year, imdb_id, file_name)
                    return True
        except Exception, e:
            logger.warning(u'Found and exception while matching file with tmdb : %s' % repr(e))
        self.move_to_unsorted(self.data_dir, file_name)
        return False

    def move_to_unsorted(self, file_dir, file_name=''):
        try:
            file_name_ext = file_name
            if not file_name:
                file_name_ext = file_dir.split('/')[-1]
            if os.path.exists(os.path.join(self.unsorted_dir, file_name_ext)):
                os.remove(os.path.join(self.unsorted_dir, file_name_ext))

            if file_name:
                os.rename(os.path.join(file_dir, file_name), os.path.join(self.unsorted_dir, file_name_ext))
            else:
                os.rename(file_dir, os.path.join(self.unsorted_dir, file_name_ext))
        except OSError:
            logger.error(u'Can\'t create %s' % file_name)

    def create_dir_and_move_movie(self, movie_name, year, imdb_id, filename):
        # Because Wall-e was WALL*E for some reason...and : isn't supported on winos...
        movie_name = re.sub('[\*\:]', '-', movie_name)
        file_path = os.path.join(self.data_dir, filename)

        custom_movie_dir = "%s (%s)" % (movie_name, year)
        quality = get_quality(filename)
        if quality:
            custom_movie_dir += ' [' + quality + ']'
        try:
            exist, movie = get_movie(movie_name, year=year)
            if exist and os.path.exists(movie.abs_folder_path):
                if movie.file_size > os.path.getsize(file_path):
                    logger.info(u'Do not sort as already existing bigger movie exists')
                    self.move_to_unsorted(file_path)
                    return False
                elif movie.file_size == os.path.getsize(file_path):
                    logger.info(u'Same size movie exists, deleting source')
                    tools.delete_dir(file_path)
                    return False
                else:
                    logger.info(u'Moving the old movie folder to unsorted as new file is bigger')
                    self.move_to_unsorted(movie.abs_folder_path)
            logger.debug(u'Custom folder name :%s' % custom_movie_dir)
            created_movie_dir = tools.make_dir(os.path.join(self.alphabetical_movie_dir, custom_movie_dir))
            logger.debug(u'Created folder path :%s' % created_movie_dir)
            if movie:
                movie.year = year or ''
                movie.folder_path = created_movie_dir
                movie.save()
                logger.info(u'Existing Movie object updated')
            else:
                movie = insert_movie(movie_name, year, created_movie_dir, os.path.getsize(file_path))
                logger.info(u'Created Movie object')
            if imdb_id:
                movie.imdb_id = imdb_id
                movie.save()
            new_name = re.sub('.*(\.[a-zA-Z0-9]*)$', '%s\g<1>' % re.sub(' ', '.', custom_movie_dir), filename)
            logger.info(u'Moving %s, with new name %s' % (filename, new_name))
            os.rename(file_path, os.path.join(created_movie_dir, new_name))
            return True
        except OSError:
            logger.error(u'Can\'t create %s' % custom_movie_dir)
        except Exception, e:
            logger.exception(u'Found an exception when moving movie : %s' % repr(e))
        return False


def get_size(file_name):
    return os.path.getsize(os.path.abspath(file_name))


def get_dir_size(dir_name):
    # TODO : Write unite test for that method
    return sum([get_size(os.path.join(dir_name, x)) for x in os.listdir(dir_name)]) if os.path.exists(dir_name) else 0


def get_info(name):
    regex_res = re.match('(.+)(20[01][0-9]|19[5-9][0-9])', name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        result = dict(title=title)
        result['year'] = regex_res.group(2)
        return result

    regex_res = re.match('(.+)(?:720p?|1080p?)', name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        return dict(title=title)

    regex_res = re.match('^(.+).{4}$', name)
    title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
    return dict(title=title)


def get_quality(name):
    quality = []
    regex_resolution = re.search('(720p|1080p)', name)
    if regex_resolution:
        quality.append(regex_resolution.group(1))

    if re.search('[aA][cC]3', name):
        quality.append('AC3')

    if re.search('DTS', name):
        quality.append('DTS')

    if re.search('([bB][lL][uU]-*[rR][aA][yY]|[bB][rR][Rr][iI][Pp])', name):
        quality.append('BluRay')

    if re.search('[wW][eE][bB]-*[RrdD][iIlL][pP]?', name):
        quality.append('WebRIP')

    return ','.join(quality)


def rename_serie(file_name):
    new_name = change_token_to_dot(file_name)
    if re.sub('[^\d]([0-3]?\d)x(\d{1,2})[^\d]', 'S\g<1>E\g<2>', new_name) is not new_name:
        new_name = re.sub('([0-3]?\d)x(\d{1,2})', 'S\g<1>E\g<2>', new_name)
    return new_name


def compare(file_name, api_result):
    logger.info(u'Comparing Opensubtitle api_result with file_name for safety')
    score = 0
    regex_result = is_serie(file_name)
    if regex_result:
        # Movie type consistency issue
        if api_result.get('MovieKind') == 'movie':
            logger.info(u'Type Inconsistent : ' + api_result.get('MovieKind') + ' expected Tv Series/Episode')
            return False, 0
        matching_pattern = re.search('(.*)[sS]0*(\d+)[eE]0*(\d+)', file_name) or re.search('(.*)(\d?\d)x(\d?\d)',
                                                                                           file_name)
        if not all([api_result.get('SeriesSeason') == matching_pattern.group(2),
                    api_result.get('SeriesEpisode') == matching_pattern.group(3)]):
            logger.info(u'SXXEXX inconsistent : S%sE%s, expected : S%sE%s' % (api_result.get('SeriesSeason'),
                                                                             api_result.get('SeriesEpisode'),
                                                                             matching_pattern.group(2),
                                                                             matching_pattern.group(3)))
            return False, 0

        # Weak comparison using letters
        api_serie_name = api_result.get('MovieName')
        title_matched = re.search('\"([^\"]*)\"', api_serie_name)
        api_serie_name = title_matched.group(1) if title_matched else api_serie_name

        if letter_coverage(matching_pattern.group(1), api_serie_name) < 65:
            return False, 0

        logger.info(u'Found a possible match')
        return True, letter_coverage(matching_pattern.group(1), api_serie_name)

    # Other case it's a movie
    if not (api_result.get('MovieKind') == 'movie'):
        logger.info(u'Type Inconsistency, found %s but expected movie' % api_result.get('MovieKind'))
        return False, 0

    # Year pattern api_result
    name_year_matching = re.search('([^\(\)]*).(20[01][0-9]|19[5-9][0-9])?', file_name)
    if name_year_matching.group(2) and not (name_year_matching.group(2) == api_result.get('MovieYear')):
        logger.info("Year Inconsistent, found %s but expected %s" %
                    (api_result.get('MovieYear'), name_year_matching.group(2)))
        return False, 0
    else:
        score += 0.10
    name_matching = re.search('([^\(\)]*).+(20[01][0-9]|19[5-9][0-9])', file_name)
    if name_matching:
        if not (letter_coverage(name_matching.group(1), api_result.get('MovieName')) > 65):
            logger.info(u'Letter inconsistency : %s, %s' %
                        (api_result.get('MovieName'), name_matching.group(1)))
            return False, 0
        else:
            score += letter_coverage(name_matching.group(1), api_result.get('MovieName'))
    logger.info(u'Found a perfect match')

    return True, score


def get_best_match(api_result_list, file_name):
    scores = []
    for api_result in api_result_list:
        matching, score = compare(file_name.lower(), api_result)
        if matching:
            logger.info(u'Comparison returned true, moving on')
            scores.append((matching, score, api_result))
        else:
            logger.info(u'Comparison returned false, inconsistencies exist')

    scores = sorted(scores, key=(lambda x: x[2]))
    if scores and scores[0][1] > 0:
        return scores[0][2]
    else:
        return None


def is_serie(name):
    return re.match('.*[sS](\d\d)[Ee](\d\d).*', name) or re.match('.*(\d?\d)x(\d?\d).*', name)


def change_token_to_dot(string):
    return re.sub('[^a-zA-Z0-9]+', '.', string)


def format_serie_name(serie_name):
    serie_name_token = change_token_to_dot(serie_name).split('.')
    return str.strip(' '.join([str(x).capitalize() for x in serie_name_token]))


def apply_custom_renaming(serie_name):
    lower_serie_name = serie_name.lower()
    logger.info(u'Custom renaming :%s' % lower_serie_name)
    for old, new in settings.CUSTOM_RENAMING.items():
        old = old.lower()
        new = new.lower()
        logger.debug(u'Applying filter : %s -> %s' % (old, new))
        result = re.sub(old, new, lower_serie_name)
        if not (result == lower_serie_name):
            logger.debug(u'Renamed : %s to %s' % (lower_serie_name, result))
            return result
    return serie_name


def letter_coverage(file_name, api_name):
    file_letter_count = {}
    for letter in file_name.lower():
        if letter.isalnum():
            file_letter_count[letter] = file_letter_count.get(letter, 0) + 1.0

    api_letter_count = {}
    for letter in api_name.lower():
        if letter.isalnum():
            api_letter_count[letter] = api_letter_count.get(letter, 0) + 1.0

    small = file_letter_count
    big = api_letter_count
    if len(small) > len(big):
        small = api_letter_count
        big = file_letter_count

    try:
        percent_coverage = 0.0
        for letter in small:
            if small[letter] > big.get(letter, 0.0):
                ratio = big.get(letter, 0.0) / small[letter]
            else:
                ratio = small[letter] / big[letter]
            percent_coverage += 100 * ratio * small[letter] / sum(big.values())

        name_size_factor = float(len(file_name)) / len(api_name)

        if name_size_factor > 1:
            name_size_factor = 1 / name_size_factor
        set_size_factor = float(len(small)) / len(big)

        size_factor = set_size_factor * name_size_factor

        return percent_coverage * size_factor
    except ZeroDivisionError:
        logger.exception(u'Empty title name, can\'t compare')
        return 0
