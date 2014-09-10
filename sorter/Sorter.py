__author__ = 'Alexis Durand'
import os
import re
import sys
import logging
import tools
import settings
import movieinfo.hashTool as ht

from middleware import mii_mongo
from tools import OpensubtitleWrapper

""" Sorter Module """
logger = logging.getLogger("NAS")


class Sorter:

    def __init__(self, media_dir):
        self.hash_array = []
        self.map = {}
        self.media_dir = media_dir
        self.data_dir = os.path.join(media_dir, "data")
        self.serie_dir = os.path.join(media_dir, "TVSeries")
        self.movie_dir = os.path.join(media_dir, "Movies")
        self.unsorted_dir = os.path.join(media_dir, "unsorted")
        self.alphabetical_movie_dir = os.path.join(self.movie_dir, "All")
        self.serie_regex = re.compile('[sS]0*(\d+)[eE](\d\d)')
        tools.make_dir(self.serie_dir)
        tools.make_dir(self.movie_dir)
        tools.make_dir(self.alphabetical_movie_dir)
        tools.make_dir(self.unsorted_dir)

    def create_hash_list(self, media):
        file_path = os.path.join(self.data_dir, media)
        movie_hash = str(ht.hashFile(file_path))
        self.map[movie_hash] = media
        self.hash_array.append(movie_hash)

    def sort(self):
        logger.info("Login in the wrapper")
        #OpensubtitleWrapper.log_in(True, 10)
        logger.info("Beginning Sorting")
        for media in os.listdir(self.data_dir):
            self.create_hash_list(media)

        for movie_hash in self.hash_array:
            file_name = self.map.get(movie_hash)
            result = OpensubtitleWrapper.get_subtitles(movie_hash,
                                                       str(get_size(os.path.join(self.data_dir, file_name))),
                                                       "")
            is_sorted = False
            if result:
                logger.info("Got Result from opensubtitle for %s" % file_name)
                logger.debug(result)
                if isinstance(result, list):
                    result = get_best_match(result, file_name)
                if result:
                    is_sorted = self.sort_open_subtitle_info(result)
            else:
                result = OpensubtitleWrapper.get_movie_names2([movie_hash])
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
                    logger.info("Probably a Movie? %s" % file_name)
                    self.sort_movie_from_name(file_name)

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

    def create_dir_and_move_serie(self, serie_name, serie_season, serie_episode_number, serie_title, file_name):
            serie_name = format_serie_name(apply_custom_renaming(serie_name))
            serie_title = format_serie_name(serie_title)
            extension = file_name[-4:]
            if len(serie_episode_number) < 2:
                serie_episode_number = '0' + serie_episode_number

            serie_season_number = serie_season
            if len(serie_season) < 2:
                serie_season_number = '0' + serie_season

            new_file_name = "%s.S%sE%s.%s." % (serie_name, serie_season_number, serie_episode_number, serie_title)
            quality = get_quality(file_name)
            if quality:
                new_file_name += " [%s]" % quality
            new_file_name += extension
            new_file_name = re.sub(" +", ".", new_file_name)
            new_file_name = re.sub("\.+", ".", new_file_name)
            result_dir = tools.make_dir(os.path.join(self.serie_dir, serie_name))
            episode_dir = tools.make_dir(os.path.join("%s%sSeason %s" % (result_dir, os.path.sep, serie_season)))
            try:

                existing_episode = get_episode(episode_dir, serie_name, serie_episode_number)
                if existing_episode:
                    if os.path.getsize(os.path.join(episode_dir, existing_episode)) >=\
                            os.path.getsize(os.path.join(self.data_dir, file_name)):
                        self.move_to_unsorted(self.data_dir, file_name)
                        logger.info("Moving the source to unsorted, episode already exists :%s" % existing_episode)
                    else:
                        self.move_to_unsorted(episode_dir, existing_episode)
                        logger.info("Moving destination to unsorted (because bigger = better): %s" % new_file_name)
                        os.rename(os.path.join(self.data_dir, file_name), os.path.join(episode_dir, new_file_name))
                    return True
                else:
                    logger.info("Moving the episode to the correct folder...%s" % new_file_name)
                    os.rename(os.path.join(self.data_dir, file_name), os.path.join(episode_dir, new_file_name))
                    return True
            except (WindowsError, OSError):
                logger.error(("Can't move %s" % os.path.join(self.data_dir, file_name)))
                logger.error(sys.exc_info()[1])
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
        result = mii_mongo.get_or_sync_movie_name(name, year)
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

                imdb_id = tools.MovieDBWrapper.get_movie_imdb_id(movie_id)
                logger.debug("Matching (id/imdb)  %s/%s" % (movie_id, imdb_id))
                if imdb_id:
                    imdb_id = imdb_id.get("imdb_id")
                    self.create_dir_and_move_movie(result['title'], year, imdb_id, file_name)
                    return True
        except Exception, e:
            logger.exception('Found and exception while matching file with tmdb : %s' % repr(e))
        self.move_to_unsorted(self.data_dir, file_name)
        return False

    def move_to_unsorted(self, file_dir, file_name):
        try:
            if os.path.exists(os.path.join(self.unsorted_dir, file_name)):
                os.remove(os.path.join(self.unsorted_dir, file_name))
            os.rename(os.path.join(file_dir, file_name), os.path.join(self.unsorted_dir, file_name))
        except (WindowsError, OSError):
            logger.error("Can't create %s" % file_name)
            logger.error(sys.exc_info()[1])

    def create_dir_and_move_movie(self, movie_name, year, imdb_id, filename):
        #Because Wall-e was WALL*E for some reason...and : isn't supported on winos...
        movie_name = re.sub("[\*\:]", "-", movie_name)
        #TODO: Find if moving is already existing in the folder
        if self.resolve_existing_conflict(movie_name,
                                          get_size(os.path.join(self.data_dir, filename)),
                                          self.alphabetical_movie_dir):
            return False #Return false if there's no need to do anything
        custom_movie_dir = "%s (%s)" % (movie_name, year)
        quality = get_quality(filename)
        if quality:
            custom_movie_dir += " [" + quality + "]"
        try:
            created_movie_dir = tools.make_dir(os.path.join(self.alphabetical_movie_dir, custom_movie_dir))
            if imdb_id:
                open(os.path.join(created_movie_dir, ".IMDB_ID_%s" % imdb_id), "w")
            new_name = re.sub(".*(\.[a-zA-Z0-9]*)$", "%s\g<1>" % re.sub(" ", ".", custom_movie_dir), filename)
            logger.info("Moving %s, with new name %s" % (filename, new_name))
            os.rename(os.path.join(self.data_dir, filename), os.path.join(created_movie_dir, new_name))
            return True
        except (WindowsError, OSError):
            logger.error("Can't create %s" % custom_movie_dir)
            logger.error(sys.exc_info()[1])
        except Exception, e:
            logger.exception('Found an exception when moving movie : %s' % repr(e))
        return False

    def resolve_existing_conflict(self, movie_name, file_size, movie_dir):
        #TODO: replace with db query when implemented
        for movie in os.listdir(movie_dir):
            if re.match('%s.\(\d{4}\)' % movie_name, movie):
                if get_dir_size(os.path.join(movie_dir, movie)) > file_size:
                    raise Exception('Do not sort as already existing bigger movie exists')
                else:
                    self.move_to_unsorted(movie_dir, movie)
                    logger.info('Moving the old movie folder to unsorted as new file is bigger')
                    return False


def get_size(file_name):
    return os.path.getsize(os.path.abspath(file_name))


def get_dir_size(dir_name):
    #TODO : Write unite test for that method
    return sum([get_size(os.path.join(dir_name, x)) for x in os.listdir(dir_name)])


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


def get_episode(episode_dir, serie_name, number):
    for episode in os.listdir(episode_dir):
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
    if is_serie(file_name):
        #Movie type consistency issue
        if api_result.get("MovieKind") == "movie":
            logger.info("Type Inconsistent : " + api_result.get("MovieKind") + " expected Tv Series/Episode")
            return False
        matching_pattern = re.search("(.*)[sS]0*(\d+)[eE]0*(\d+)", file_name)
        if not all([api_result.get("SeriesSeason") == matching_pattern.group(2),
                    api_result.get("SeriesEpisode") == matching_pattern.group(3)]):
            logger.info("SXXEXX inconsistent : S%sE%s, expected : S%sE%s" % (api_result.get("SeriesSeason"),
                                                                             api_result.get("SeriesEpisode"),
                                                                             matching_pattern.group(2),
                                                                             matching_pattern.group(3)))
            return False

        #Weak comparison using letters
        if letter_coverage(matching_pattern.group(1), api_result.get('MovieName')) < 0.65:
            return False

        logger.info("Found a perfect match")
        return True

    #Other case it's a movie
    if not (api_result.get("MovieKind") == "movie"):
        logger.info("Type Inconsistent : " + api_result.get("MovieKind") + " expected movie")
        return False

    #Year pattern api_result
    name_year_matching = re.search("([^\(\)]*).(20[01][0-9]|19[5-9][0-9])?", file_name)
    if name_year_matching.group(2) and not(name_year_matching.group(2) == api_result.get("MovieYear")):
        logger.info("Year Inconsistent : %s, expected year : %s" %
                    (api_result.get("MovieYear"), name_year_matching.group(2)))
        return False

    if not (letter_coverage(name_year_matching.group(1), api_result.get('MovieName')) > 0.65):
        logger.info("Letter inconsistency : %s, %s" %
                    (api_result.get("MovieName"), name_year_matching.group(1)))
        return False

    logger.info("Found a perfect match")
    return True


def get_best_match(api_result_list, file_name):
    for api_result in api_result_list:
        if compare(file_name.lower(), api_result):
            logger.info("Comparison returned true, moving on")
            return api_result
        else:
            logger.info("Comparison returned false, inconsistencies exist")
    return None


def is_serie(name):
    return re.match(".*[sS]\d\d[Ee]\d\d.*", name)


def change_token_to_dot(string):
    return re.sub("[^a-zA-Z0-9]+", ".", string)


def format_serie_name(serie_name):
    serie_name_token = change_token_to_dot(serie_name).split(".")
    return str.strip(' '.join(map(str.capitalize, serie_name_token)))


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
                ratio = big.get(letter, 1.0) / small[letter]
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


