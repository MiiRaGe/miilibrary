__author__ = 'Alexis Durand'
import os
import re
import sys
import logging
import Tool
import settings
import movieinfo.hashTool as ht

from Tool import OpensubtitleWrapper

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
        Tool.make_dir(self.serie_dir)
        Tool.make_dir(self.movie_dir)
        Tool.make_dir(self.alphabetical_movie_dir)
        Tool.make_dir(self.unsorted_dir)

    def create_hash_list(self, media):
        file_path = os.path.join(self.data_dir, media)
        movie_hash = str(ht.hashFile(file_path))
        self.map[movie_hash] = media
        self.hash_array.append(movie_hash)

    def sort(self):
        logger.info("Login in the wrapper")
        OpensubtitleWrapper.logIn(True, 10)
        logger.info("Beginning Sorting")
        for media in os.listdir(self.data_dir):
            self.create_hash_list(media)

        for movie_hash in self.hash_array:
            file_name = self.map.get(movie_hash)
            result = OpensubtitleWrapper.get_subtitles(movie_hash,
                                                       self.get_size(os.path.join(self.data_dir, file_name)),
                                                       "")
            is_sorted = False
            if result:
                logger.info("Got Result from opensubtitle for " + file_name)
                logger.debug(result)
                if type(result) == list:
                    result = self.get_best_match(result, file_name)
                if result:
                    is_sorted = self.sort_open_subtitle_info(result)
            else:
                result = OpensubtitleWrapper.getMovieNames2([movie_hash])
                if result:
                    logger.info(result)
                    result = result.get(movie_hash)
                    if type(result) == list:
                        result = self.get_best_match(result, file_name)
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
            serie_name = format_serie_name(self.apply_custom_renaming(serie_name))
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
            result_dir = Tool.make_dir(os.path.join(self.serie_dir, serie_name))
            episode_dir = Tool.make_dir(os.path.join("%s%sSeason %s" % (result_dir, os.path.sep, serie_season)))
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
        result = Tool.MovieDBWrapper.getMovieName(name, year)
        logger.debug("Result from tmdb: %s" % result)
        if result:
            result = result[0]
            movie_id = str(result.get("id"))
            logger.debug("Found Id : " + movie_id )
            imdb_id = Tool.MovieDBWrapper.get_movie_imdb_id(movie_id)
            if imdb_id:
                imdb_id = imdb_id.get("imdb_id")
                self.create_dir_and_move_movie(result.get("title"), year, imdb_id, file_name)
                return True
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

    def create_dir_and_move_movie(self, movie_name, year, imdbid, filename):
        #Because Wall-e was WALL*E for some reason...and : isn't supported on winos...
        movie_name = re.sub("[\*\:]", "-", movie_name)
        custom_movie_dir = "%s (%s)" % (movie_name, year)
        quality = get_quality(filename)
        if quality:
            custom_movie_dir += " [" + quality + "]"
        try:
            created_movie_dir = Tool.make_dir(os.path.join(self.alphabetical_movie_dir, custom_movie_dir))
            if imdbid:
                open(os.path.join(created_movie_dir, ".IMDB_ID_%s" % imdbid), "w")
            new_name = re.sub(".*(\.[a-zA-Z0-9]*)$", "%s\g<1>" % re.sub(" ", ".", custom_movie_dir), filename)
            logger.info("Moving %s, with new name %s" % (filename, new_name))
            os.rename(os.path.join(self.data_dir, filename), os.path.join(created_movie_dir, new_name))
            return True
        except (WindowsError, OSError):
            logger.error("Can't create %s" % custom_movie_dir)
            logger.error("Probably because windows naming convention sucks, skipping...")
            logger.error(sys.exc_info()[1])
            return False

    def get_size(self, file_name):
        return str(os.path.getsize(os.path.join(self.data_dir, file_name)))


def get_info(name):
    regex_res = re.match("(.*)(20[01][0-9]|19[5-9][0-9]).*", name)
    if regex_res:
        title = re.sub('\.', ' ', change_token_to_dot(regex_res.group(1))).strip()
        result = {"title": title,
                  "year": regex_res.group(2)}
        return result
    return None


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


def compare(file_name, result):
    logger.info("Comparing Opensubtitle result with file_name for safety")
    if is_serie(file_name):
        #Movie type consistency issue
        if result.get("MovieKind") == "movie":
            logger.info("Type Inconsistent : " + result.get("MovieKind") + " expected Tv Series/Episode")
            return False
        matching_pattern = re.search("[sS]0*(\d+)[eE]0*(\d+)", file_name)
        if not (result.get("SeriesSeason") == matching_pattern.group(1)) or\
                not(result.get("SeriesEpisode") == matching_pattern.group(2)):
            logger.info("SXXEXX inconsistent : S%sE%s, expected : S%sE%s" % (result.get("SeriesSeason"),
                                                                             result.get("SeriesEpisode"),
                                                                             matching_pattern.group(1),
                                                                             matching_pattern.group(2)))
            return False
        #Otherwise it should be safe
        return True
    #Other case it's a movie
    if not (result.get("MovieKind") == "movie"):
        logger.info("Type Inconsistent : " + result.get("MovieKind") + " expected movie")
        return False
    #Year pattern result
    year_matching = re.search("(20[01][0-9]|19[5-9][0-9])", file_name)
    if year_matching and not(year_matching.group(1) == result.get("MovieYear")):
        logger.info("Year Inconsistent : %s, expected year : %s" %
                    (result.get("MovieYear"), year_matching.group(1)))
        return False

    #Otherwise it should be ok
    return True


def get_best_match(result_list, filename):
    for result in result_list:
        if compare(filename, result):
            logger.info("Comparison returned true, moving on")
            return result
        else:
            logger.info("Comparison returned false, inconsistencies exist")
    return None


def is_serie(self, name):
        return re.match(".*[sS]\d\d[Ee]\d\d.*", name)


def change_token_to_dot(string):
    return re.sub("[^a-zA-Z0-9]*", ".", string)


def format_serie_name(serie_name):
    serie_name_token = change_token_to_dot(serie_name).split(".")
    return str.strip(' '.join(map(str.capitalize, serie_name_token)))


def apply_custom_renaming(serie_name):
    lower_serie_name = serie_name.lower()
    logger.info("Custom renamming :%s" % lower_serie_name)
    for old, new in settings.CUSTOM_RENAMING.items():
        logger.debug("Applying filter : %s -> %s" % (old, new))
        result = re.sub(old, new, lower_serie_name)
        if not (result == lower_serie_name):
            logger.debug("Renamed : %s to %s" % (lower_serie_name, result))
            return result
    return serie_name