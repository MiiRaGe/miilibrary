import logging
import re
import os

from collections import defaultdict
from copy import deepcopy
from pprint import pprint

from mii_common import tools

from middleware import mii_mongo
from mii_indexer.models import Tag, MovieTagging, Person, MovieRelation


logger = logging.getLogger("NAS")


class Indexer:
    def __init__(self, source_dir):
        # All directory is always created by sorter and contains all movie sorted alphabetically
        self.mii_osdb = mii_mongo.MiiOpenSubtitleDB()
        self.source_dir = source_dir
        self.alphabetical_dir = os.path.join(source_dir, "All")
        self.search_dir = os.path.join(source_dir, "Search")
        self.index_mapping = {
            'genre_dir': (os.path.join(source_dir, 'Genres'), lambda x: x.get('genres'), 'Tag'),
            'rating_dir': (os.path.join(source_dir, 'Ratings'), lambda x: [str(int(float(x.get('rating', 0))))], 'Rating'),
            'year_dir': (os.path.join(source_dir, 'Years'), lambda x: [x.get('year')], 'Year'),
            'director_dir': (os.path.join(source_dir, 'Directors'), lambda x: x.get('directors', {}).values(), 'Director'),
            'actor_dir': (os.path.join(source_dir, 'Actors'), lambda x: x.get('cast', {}).values(), 'Actor')
        }

    def init(self):
        for folder, _, type in self.index_mapping.values() + [(self.search_dir, None, 'Search')]:
            tools.delete_dir(folder)
            tools.make_dir(folder)

    def index(self):
        logger.info("****************************************")
        logger.info("**********      Indexer       **********")
        logger.info("****************************************")
        self.init()

        imdb_regex = re.compile('\.IMDB_ID_(?:tt)?(\d+)$')
        index = {}
        search_index_dict = {}
        for folder in os.listdir(self.alphabetical_dir):
            logger.info('------ %s ------' % folder)
            folder_abs = os.path.join(self.alphabetical_dir, folder)
            if os.path.isdir(folder_abs):
                imdb_file = None
                id = None
                for file in os.listdir(folder_abs):
                    id = imdb_regex.match(file)
                    if id:
                        logger.info('Found imdb file %s' % file)
                        break

                search_index_dict.update(dict_merge_list_extend(search_index_dict, search_index(folder)))
        add_number_and_simplify(search_index_dict)
        pprint(search_index_dict)
                # #This regex have to match, that's how it's formatted previously.
                # matched = re.match('([^\(]*) \((\d{4})\).*', folder)
                # if matched:
                #     movie_name = matched.group(1)
                #     year = matched.group(2)
                #     found, movie = mii_sql.get_movie(movie_name, year)
                # if id:
                #     imdb_data = self.mii_osdb.get_imdb_information(int(id.group(1)))
                #     if movie and not movie.imdb_id:
                #         movie.imdb_id = id.group(1)
                #         movie.save()
                #     if imdb_data:
                #         logger.info('Found imdb data from opensubtitle:')
                #         logger.debug("\tData: %s" % imdb_data)
                #         for index in self.index_mapping.keys():
                #             self.index_values(self.index_mapping[index][1](imdb_data), folder, folder_abs, index,
                #                               movie=movie)
        # self.add_counting(self.search_dir, skipped=True)
        # self.remove_single_movie_person()

    def remove_single_movie_person(self):
        for folder in tools.listdir_abs(self.index_mapping['director_dir'][0]) +\
                tools.listdir_abs(self.index_mapping['actor_dir'][0]):
            if len(os.listdir(folder)) <= 1:
                tools.delete_dir(folder)

    def index_values(self, values, folder, folder_abs, index_dir, movie=None):
        if values:
            logger.info('\tIndexing %s, with %s' % (folder, values))
            try:
                for value in values:
                    value = value.strip()
                    tools.make_dir(os.path.join(self.index_mapping[index_dir][0], value))
                    os.symlink(folder_abs, os.path.join(self.index_mapping[index_dir][0], value, folder))
                    if movie:
                        self.link_movie_value(movie, value, self.index_mapping[index_dir][2])

            except Exception, e:
                logger.exception("With exception :%s" % repr(e))

    def add_counting(self, current_folder, skipped=False):
        for folder in os.listdir(current_folder):
            if folder != '--':
                count = len(os.listdir(os.path.join(current_folder, folder, '--')))
                self.add_counting(os.path.join(current_folder, folder))
                os.rename(os.path.join(current_folder, folder),
                          os.path.join(current_folder, '%s (%s results)' % (folder, count)))
        if not skipped:
            self._add_counting(current_folder)

    @staticmethod
    def _add_counting(current_dir):
        count = len(os.listdir(os.path.join(current_dir, '--')))
        if count > 1:
            os.rename(os.path.join(current_dir, '--'), os.path.join(current_dir, '-- (%s results)' % count))
        else:
            for folder in tools.listdir_abs(current_dir):
                if folder.endswith('--'):
                    os.rename(os.path.join(folder, os.listdir(folder)[0]),
                              os.path.join(current_dir, os.listdir(folder)[0]))
                tools.delete_dir(folder)

    @staticmethod
    def link_movie_value(movie, value, link_type):
        if link_type == 'Tag':
            tag = Tag.get_or_create(name=value)
            MovieTagging.get_or_create(tag=tag, movie=movie)
        elif link_type == 'Year':
            movie.year = value
            movie.save()
        elif link_type == 'Rating':
            movie.rating = value
            movie.save()
        elif link_type in ['Actor', 'Director']:
            person = Person.get_or_create(name=value)
            uid = '%s.%s.%s' % (person.id, movie.id, link_type)
            try:
                MovieRelation.get(uid=uid)
            except MovieRelation.DoesNotExist:
                link = MovieRelation.create(uid=uid, person=person, movie=movie, type=link_type)
                logger.debug('Link is saved :%s,%s,%s' % (link.person.name, link.movie.title, link.type))


def search_index(folder):
    matched = re.match('(^[^\(]*)\(.*', folder)
    if matched:
        name = matched.group(1)
    else:
        name = folder
    return get_tree_from_list([x.upper() for x in name if x.isalpha()], folder)


def get_tree_from_list(remaining_letters, folder):
    if not remaining_letters:
        return {'--': [folder]}
    return {remaining_letters[0]: get_tree_from_list(remaining_letters[1:], folder),
            '--': [folder]}

    os.symlink(folder_abs, os.path.join(result_folder, folder))


def dict_merge_list_extend(d1, d2):
    for key, value in d2.items():
        if not d1.get(key):
            d1[key] = value
            continue
        if isinstance(d1.get(key), list):
            d1[key].extend(value)
        else:
            d1[key] = dict_merge_list_extend(d1[key], value)
    return d1


def add_number_and_simplify(d1):
    for key in d1.keys():
        count = get_count(d1[key])
        new_value = d1.pop(key)
        if count == 1:
            d1[key + ' (1)'] = new_value if key == '--' else new_value['--']
        else:
            d1[key + ' (%s)' % count] = new_value
            if key != '--':
                add_number_and_simplify(new_value)


def get_count(d1):
    if isinstance(d1, list):
        return len(d1)
    else:
        return len(d1.get('--', []))