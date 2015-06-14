from collections import defaultdict
import logging
import re
import os

from pprint import pprint

from mii_common import tools

from middleware import mii_mongo
from mii_indexer.models import Tag, MovieTagging, Person, MovieRelation
from mii_sorter.models import get_movie


logger = logging.getLogger("NAS")


class Indexer:
    mii_osdb = mii_mongo.MiiOpenSubtitleDB()

    def __init__(self, source_dir):
        # All directory is always created by sorter and contains all movie sorted alphabetically
        self.source_dir = source_dir
        self.alphabetical_dir = os.path.join(source_dir, "All")
        self.search_dir = os.path.join(source_dir, "Search")
        self.index_mapping = {
            'genre_dir': ('Genres', lambda x: x.get('genres'), 'Tag'),
            'rating_dir': ('Ratings', lambda x: [str(int(float(x.get('rating', 0))))], 'Rating'),
            'year_dir': ('Years', lambda x: [x.get('year')], 'Year'),
            'director_dir': ('Directors', lambda x: x.get('directors', {}).values(), 'Director'),
            'actor_dir': ('Actors', lambda x: x.get('cast', {}).values(), 'Actor')
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

        index_dict = defaultdict(dict)
        for folder in os.listdir(self.alphabetical_dir):
            logger.info('------ %s ------' % folder)
            folder_abs = os.path.join(self.alphabetical_dir, folder)
            if os.path.isdir(folder_abs):
                imdb_file = None
                id = None

                index_dict['Search'].update(dict_merge_list_extend(index_dict['Search'], search_index((folder, folder_abs,))))
                matched = re.match('([^\(]*) \((\d{4})\).*', folder)
                if matched:
                    movie_name = matched.group(1)
                    year = matched.group(2)
                    found, movie = get_movie(movie_name, year)

                if movie and movie.imdb_id:
                    imdb_id = movie.imdb_id
                    imdb_data = self.mii_osdb.get_imdb_information(imdb_id)
                    if imdb_data:
                        logger.info('Found imdb data from opensubtitle:')
                        logger.debug("\tData: %s" % imdb_data)
                        for index_type, value in self.index_mapping.items():
                            new_index_for_movie = self.index_values(self.index_mapping[index_type][1](imdb_data),
                                                                    folder,
                                                                    folder_abs,
                                                                    index_type,
                                                                    movie=movie)
                            index_dict[value[0]].update(dict_merge_list_extend(index_dict[value[0]], new_index_for_movie))

        index_dict['Search'] = add_number_and_simplify(index_dict['Search'])
        remove_single_movie_person(index_dict)
        pprint(index_dict)

    def index_values(self, values, folder, folder_abs, index_type, movie=None):
        if values:
            index_dict = {}
            logger.info('\tIndexing %s, with %s' % (folder, values))
            try:
                for value in values:
                    value = value.strip()
                    index_dict[value] = [(folder, folder_abs)]
                    if movie:
                        self.link_movie_value(movie, value, self.index_mapping[index_type][0])
            except Exception, e:
                logger.exception("With exception :%s" % repr(e))
            return index_dict

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
            tag, created = Tag.objects.get_or_create(name=value)
            MovieTagging.objects.get_or_create(tag=tag, movie=movie)
        elif link_type == 'Year' and not movie.year:
            movie.year = value
            movie.save()
        elif link_type == 'Rating' and not movie.rating:
            movie.rating = value
            movie.save()
        elif link_type in ['Actor', 'Director']:
            person, _ = Person.objects.get_or_create(name=value)
            MovieRelation.objects.get_or_create(person=person, movie=movie, type=link_type)
            logger.debug('Link is saved :%s,%s,%s' % (person.name, movie.title, link_type))


def search_index(folder):
    matched = re.match('(^[^\(]*)\(.*', folder[0])
    if matched:
        name = matched.group(1)
    else:
        name = folder[0]
    return get_tree_from_list([x.upper() for x in name if x.isalpha()], folder)


def get_tree_from_list(remaining_letters, folder):
    if not remaining_letters:
        return {'--': [folder]}
    return {remaining_letters[0]: get_tree_from_list(remaining_letters[1:], folder),
            '--': [folder]}

    tools.make_dir(os.path.join(self.index_mapping[index_type][0], value))
    os.symlink(folder_abs, os.path.join(self.index_mapping[index_type][0], value, folder))
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


def remove_single_movie_person(index_dict):
    for actor, value in index_dict['Actor'].items():
        if len(value) <= 1:
            del index_dict['Actor'][actor]
