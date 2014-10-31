import logging
import os
import re

import movieinfo.hashTool as ht
import settings
import tools

from middleware import mii_mongo, mii_sql

""" Sorter Module """
logger = logging.getLogger("NAS")

try:
    raise WindowsError
except NameError:
    WindowsError = None
except Exception:
    pass


class Sorter:
    def __init__(self, media_dir):
        self.hash_array = []
        self.map = {}
        self.media_dir = media_dir
        self.data_dir = os.path.join(media_dir, "data")
        self.whatsnew_dir = tools.make_dir(os.path.join(self.media_dir, "What's New"))
        self.serie_dir = os.path.join(media_dir, "TVSeries")
        self.movie_dir = os.path.join(media_dir, "Movies")
        self.unsorted_dir = os.path.join(media_dir, "unsorted")
        self.alphabetical_movie_dir = os.path.join(self.movie_dir, "All")
        self.serie_regex = re.compile('[sS]0*(\d+)[eE](\d\d)')
        self.mii_tmdb = mii_mongo.MiiTheMovieDB()
        self.mii_osdb = mii_mongo.MiiOpenSubtitleDB()
        tools.make_dir(self.serie_dir)
        tools.make_dir(self.movie_dir)
        tools.make_dir(self.alphabetical_movie_dir)
        tools.make_dir(self.unsorted_dir)

    def create_hash_list(self, media):
        file_path = os.path.join(self.data_dir, media)
        movie_hash = str(ht.hashFile(file_path))
        self.map[movie_hash] = media
        self.hash_array.append(movie_hash)
        self.hash_array = list(set(self.hash_array))

    def sort(self):
        logger.info("****************************************")
        logger.info("**********       Sorter       **********")
        logger.info("****************************************")
        #TODO optimize sorting
        self.map = {}
        self.hash_array = []
        for media in os.listdir(self.data_dir):
            self.create_hash_list(media)

        for movie_hash in sorted(self.hash_array):
            file_name = self.map.get(movie_hash)
            logger.info('------ %s ------' % file_name)
            result = self.mii_osdb.get_subtitles(movie_hash,
                                                 str(get_size(os.path.join(self.data_dir, file_name))))
            is_sorted = False
            if result:
                logger.info("Got Result from opensubtitle for %s" % file_name)
                #logger.debug(result)
                if isinstance(result, list):
                    result = get_best_match(result, file_name)
                if result:
                    is_sorted = self.sort_open_subtitle_info(result)
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
                    logger.info("Sorted the TV Serie : %s" % file_name)
                else:
                    logger.info("Looks like a movie")
                    self.sort_movie_from_name(file_name)

        self.update_whatsnew()

    def update_whatsnew(self):
        tools.delete_dir(self.whatsnew_dir)
        self.whatsnew_dir = tools.make_dir(os.path.join(self.media_dir, "What's New"))
        for whatsnew in mii_sql.WhatsNew.select().order_by('date').limit(10):
            os.symlink(whatsnew.path, os.path.join(self.whatsnew_dir, whatsnew.name))


    def sort_open_subtitle_info(self, result):
        file_name = self.map.get(result.get("MovieHash"))
        if result.get("MovieKind") == 'movie':
            return self.create_dir_and_move_movie(result.get("MovieName"),
                                                  result.get("MovieYear"),
                                                  result.get("IDMovieImdb"),
                                                  file_name)
        else:
            parsing = re.match('"(.*)"(.*)', result.get("MovieName"))
            serie_title = ""
            if parsing:
                serie_name = parsing.group(1).strip()
                serie_title = parsing.group(2).strip()
            else:
                serie_name = result.get("MovieName")

            if result.get("SeriesSeason") == '0' or result.get("SeriesEpisode") == '0':
                matched = self.serie_regex.search(result.get('SubFileName'))
                if matched:
                    result["SeriesSeason"] = matched.group(1)
                    result["SeriesEpisode"] = matched.group(2)
            return self.create_dir_and_move_serie(serie_name,
                                                  result.get("SeriesSeason"),
                                                  result.get("SeriesEpisode"),
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

        new_file_name = "%s.S%sE%s.%s." % (name, serie_season_number, episode_number, title)
        quality = get_quality(file_name)
        if quality:
            new_file_name += " [%s]" % quality
        new_file_name += extension
        new_file_name = re.sub("[\s\.]+", ".", new_file_name)
        result_dir = tools.make_dir(os.path.join(self.serie_dir, name))
        season_dir = tools.make_dir(os.path.join("%s/Season %s" % (result_dir, season)))
        try:
            exists, serie = mii_sql.get_serie_episode(name, int(season), int(episode_number))
            existing_episode = get_episode(season_dir, name, episode_number)
            file_path = os.path.join(self.data_dir, file_name)

            if exists and os.path.exists(serie.file_path):
                if serie.file_size > os.path.getsize(file_path):
                    self.move_to_unsorted(file_path)
                    logger.info("Moving the source to unsorted, episode already exists :%s" % serie.file_path)
                elif serie.file_size == os.path.getsize(file_path):
                    os.remove(file_path)
                    logger.info("Removed the source, episode already exists and same size:%s" % existing_episode)
                else:
                    self.move_to_unsorted(serie.file_path)
                    logger.info("Moving destination to unsorted (because bigger = better): %s" % new_file_name)
                    os.rename(file_path, os.path.join(season_dir, new_file_name))
                    serie.file_path = os.path.join(season_dir, new_file_name)
                    serie.file_size = os.path.getsize(os.path.join(season_dir, new_file_name))
                    serie.save()
                return True
            else:
                if not exists:
                    serie = mii_sql.insert_serie_episode(name,
                                                         season,
                                                         episode_number,
                                                         os.path.join(season_dir, new_file_name))
                    serie.file_size = os.path.getsize(file_path)
                    serie.save()
                    logger.info("Created Serie object %s,S%sE%s" % (name, season, episode_number))
                else:
                    serie.file_path = os.path.join(season_dir, new_file_name)
                    serie.save()
                logger.info("Moving the episode to the correct folder...%s" % new_file_name)
                os.rename(file_path, os.path.join(season_dir, new_file_name))
                return True
        except (WindowsError, OSError):
            logger.error(("Can't move %s" % file_path))
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
        name = info.get("title")
        year = info.get("year")
        logger.info("Name/Year found from file_name : Name = <%s>, Year = <%s>" % (name, year))
        result = self.mii_tmdb.get_movie_name(name, year)
        logger.debug("Result from tmdb: %s" % result)
        try:
            if result and result.get('results'):
                result = result.get('results')[0]
                movie_id = str(result.get("id"))
                logger.debug("Matching result: %s" % result)
                matching_year = result.get('release_date', '1900-01-01')
                matched = re.match('(?:\d{4})', matching_year)
                if matched:
                    if not year:
                        year = matched.group(0)
                    else:
                        if year != matched.group(0):
                            logger.error('Year not matching for %s, Got %s expected %s' % (file_name,
                                                                                           matched.group(0),
                                                                                           year))
                        else:
                            logger.info('Year matched for %s' % file_name)
                percent = letter_coverage(name, result['title'])
                if percent > 65.0:
                    logger.info('Title matched %s, %s at (%s%%)' % (name, result['title'], percent))
                else:
                    raise Exception('Title did not match %s, %s with (%s%%)' % (name, result['title'], percent))

                imdb_id = self.mii_tmdb.get_movie_imdb_id(movie_id)
                logger.debug("Matching (id/imdb)  %s/%s" % (movie_id, imdb_id))
                if imdb_id:
                    imdb_id = imdb_id.get("imdb_id")
                    self.create_dir_and_move_movie(result['title'], year, imdb_id, file_name)
                    return True
        except Exception, e:
            logger.warning('Found and exception while matching file with tmdb : %s' % repr(e))
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
        except (WindowsError, OSError):
            logger.error("Can't create %s" % file_name)

    def create_dir_and_move_movie(self, movie_name, year, imdb_id, filename):
        # Because Wall-e was WALL*E for some reason...and : isn't supported on winos...
        movie_name = re.sub("[\*\:]", "-", movie_name)
        file_path = os.path.join(self.data_dir, filename)
        try:
            exist, movie = mii_sql.get_movie(movie_name, year=year)
            if exist and os.path.exists(movie.folder_path):
                if movie.file_size > os.path.getsize(file_path):
                    logger.info('Do not sort as already existing bigger movie exists')
                    self.move_to_unsorted(file_path)
                    return False
                elif movie.file_size == os.path.getsize(file_path):
                    logger.info('Same size movie exists, deleting source')
                    tools.delete_dir(file_path)
                    return False
                else:
                    logger.info('Moving the old movie folder to unsorted as new file is bigger')
                    self.move_to_unsorted(movie.folder_path)

            custom_movie_dir = "%s (%s)" % (movie_name, year)
            quality = get_quality(filename)
            if quality:
                custom_movie_dir += " [" + quality + "]"
            logger.debug('Custom folder name :%s' % custom_movie_dir)
            created_movie_dir = tools.make_dir(os.path.join(self.alphabetical_movie_dir, custom_movie_dir))
            logger.debug('Created folder path :%s' % created_movie_dir)
            if movie:
                movie.year = year or ''
                movie.folder_path = created_movie_dir
                movie.save()
                logger.info('Existing Movie object updated')
            else:
                movie = mii_sql.insert_movie(movie_name, year, created_movie_dir)
                movie.file_size = os.path.getsize(file_path)
                movie.save()
                logger.info('Created Movie object')
            if imdb_id:
                movie.imdb_id = imdb_id
                movie.save()
                open(os.path.join(created_movie_dir, ".IMDB_ID_%s" % imdb_id), "w")
            new_name = re.sub(".*(\.[a-zA-Z0-9]*)$", "%s\g<1>" % re.sub(" ", ".", custom_movie_dir), filename)
            logger.info("Moving %s, with new name %s" % (filename, new_name))
            os.rename(file_path, os.path.join(created_movie_dir, new_name))
            return True
        except (WindowsError, OSError):
            logger.error("Can't create %s" % custom_movie_dir)
        except Exception, e:
            logger.exception('Found an exception when moving movie : %s' % repr(e))
        return False

    def resolve_existing_conflict(self, movie_name, file_size, movie_dir, year=None):
        # TODO: replace with db query when implemented
        """
        Query the db to see if movie exist, returns movie object for update if match is found
        :param string movie_name: Name of the movie
        :param int file_size: Size of the current movie
        :param string movie_dir: Path of the current movie
        :param int year: year of the movie
        :return: Movie :raise Exception: Don't sort as already existing
        :rtype: mii_sql.Movie
        """



def get_size(file_name):
    return os.path.getsize(os.path.abspath(file_name))


def get_dir_size(dir_name):
    # TODO : Write unite test for that method
    return sum([get_size(os.path.join(dir_name, x)) for x in os.listdir(dir_name)]) if os.path.exists(dir_name) else 0


def get_info(name):
    regex_res = re.match("(.+)(20[01][0-9]|19[5-9][0-9])", name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        result = {"title": title}
        try:
            result['year'] = regex_res.group(2)
        except AttributeError:
            logger.exception("No year info for %s" % name)
        return result

    regex_res = re.match("(.+)(?:720p?|1080p?)", name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        return {"title": title}

    regex_res = re.match("(.+).{4}$", name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        return {"title": title}

    return {"title": name}


def get_quality(name):
    quality = []
    regex_resolution = re.search("(720p|1080p)", name)
    if regex_resolution:
        quality.append(regex_resolution.group(1))

    if re.search("[aA][cC]3", name):
        quality.append("AC3")

    if re.search("DTS", name):
        quality.append("DTS")

    if re.search("([bB][lL][uU]-*[rR][aA][yY]|[bB][rR][Rr][iI][Pp])", name):
        quality.append("BluRay")

    if re.search("[wW][eE][bB]-*[RrdD][iIlL][pP]?", name):
        quality.append("WebRIP")

    return ','.join(quality)


def get_episode(season_dir, serie_name, number):
    for episode in os.listdir(season_dir):
        if re.search("[Ss]\d+[eE]" + number, episode):
            logger.info("Same episode found (%s e%s) : %s" % (serie_name, number, episode))
            return episode
    return None


def rename_serie(file_name):
    new_name = change_token_to_dot(file_name)
    if re.sub("[^\d]([0-3]?\d)x(\d{1,2})[^\d]", "S\g<1>E\g<2>", new_name) is not new_name:
        new_name = re.sub("([0-3]?\d)x(\d{1,2})", "S\g<1>E\g<2>", new_name)
    return new_name


def compare(file_name, api_result):
    logger.info("Comparing Opensubtitle api_result with file_name for safety")
    score = 0
    if is_serie(file_name):
        # Movie type consistency issue
        if api_result.get("MovieKind") == "movie":
            logger.info("Type Inconsistent : " + api_result.get("MovieKind") + " expected Tv Series/Episode")
            return False, 0
        matching_pattern = re.search("(.*)[sS]0*(\d+)[eE]0*(\d+)", file_name)
        if not all([api_result.get("SeriesSeason") == matching_pattern.group(2),
                    api_result.get("SeriesEpisode") == matching_pattern.group(3)]):
            logger.info("SXXEXX inconsistent : S%sE%s, expected : S%sE%s" % (api_result.get("SeriesSeason"),
                                                                             api_result.get("SeriesEpisode"),
                                                                             matching_pattern.group(2),
                                                                             matching_pattern.group(3)))
            return False, 0

        # Weak comparison using letters
        api_serie_name = api_result.get('MovieName')
        title_matched = re.search('\"([^\"]*)\"', api_serie_name)
        api_serie_name = title_matched.group(1) if title_matched else api_serie_name

        if letter_coverage(matching_pattern.group(1), api_serie_name) < 65:
            return False, 0

        logger.info("Found a possible match")
        return True, letter_coverage(matching_pattern.group(1), api_serie_name)

    # Other case it's a movie
    if not (api_result.get("MovieKind") == "movie"):
        logger.info("Type Inconsistent : " + api_result.get("MovieKind") + " expected movie")
        return False, 0

    # Year pattern api_result
    name_year_matching = re.search("([^\(\)]*).(20[01][0-9]|19[5-9][0-9])?", file_name)
    if name_year_matching.group(2) and not (name_year_matching.group(2) == api_result.get("MovieYear")):
        logger.info("Year Inconsistent : %s, expected year : %s" %
                    (api_result.get("MovieYear"), name_year_matching.group(2)))
        return False, 0
    else:
        score += 0.10
    name_matching = re.search("([^\(\)]*).+(20[01][0-9]|19[5-9][0-9])", file_name)
    if name_matching:
        if not (letter_coverage(name_matching.group(1), api_result.get('MovieName')) > 65):
            logger.info("Letter inconsistency : %s, %s" %
                        (api_result.get("MovieName"), name_matching.group(1)))
            return False, 0
        else:
            score += letter_coverage(name_matching.group(1), api_result.get('MovieName'))
    logger.info("Found a perfect match")

    return True, score


def get_best_match(api_result_list, file_name):
    scores = []
    for api_result in api_result_list:
        #TODO Get the whole list score and return the best one
        matching, score = compare(file_name.lower(), api_result)
        if matching:
            logger.info("Comparison returned true, moving on")
            scores.append((matching, score, api_result))
        else:
            logger.info("Comparison returned false, inconsistencies exist")

    scores = sorted(scores, key=(lambda x: x[2]))
    if scores and scores[0][1] > 0:
        return scores[0][2]
    else:
        return None


def is_serie(name):
    return re.match(".*[sS]\d\d[Ee]\d\d.*", name)


def change_token_to_dot(string):
    return re.sub("[^a-zA-Z0-9]+", ".", string)


def format_serie_name(serie_name):
    serie_name_token = change_token_to_dot(serie_name).split(".")
    return str.strip(' '.join([str(x).capitalize() for x in serie_name_token]))


def apply_custom_renaming(serie_name):
    lower_serie_name = serie_name.lower()
    logger.info("Custom renamming :%s" % lower_serie_name)
    for old, new in settings.CUSTOM_RENAMING.items():
        old = old.lower()
        new = new.lower()
        logger.debug("Applying filter : %s -> %s" % (old, new))
        result = re.sub(old, new, lower_serie_name)
        if not (result == lower_serie_name):
            logger.debug("Renamed : %s to %s" % (lower_serie_name, result))
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
        logger.exception("Empty title name, can't compare")
        return 0


