import json
import logging
import re
import os
from collections import defaultdict
from django.conf import settings
from django.utils.encoding import smart_unicode
from pyreport.reporter import Report
from middleware import mii_cache_wrapper
from middleware.remote_execution import symlink
from mii_common import tools
from mii_common.tools import dict_apply
from mii_indexer.models import Tag, MovieTagging, Person, MovieRelation
from mii_sorter.models import get_movie, insert_report

logger = logging.getLogger(__name__)

if settings.REPORT_ENABLED:
    logger = Report()


class Indexer:
    mii_osdb = mii_cache_wrapper.MiiOpenSubtitleDB()

    def __init__(self):
        # All directory is always created by sorter and contains all movie sorted alphabetically
        self.source_dir = os.path.join(settings.DESTINATION_FOLDER, 'Movies')
        self.alphabetical_dir = os.path.join(self.source_dir, "All")
        self.index_dir = tools.make_dir(os.path.join(self.source_dir, "Index"))
        self.index_mapping = {
            'genre_dir': ('Genres', lambda x: x.get('genres'), 'Tag'),
            'rating_dir': ('Ratings', lambda x: [str(float(x.get('rating', 0)))], 'Rating'),
            'year_dir': ('Years', lambda x: [x.get('year')], 'Year'),
            'director_dir': ('Directors', lambda x: x.get('directors', {}).values(), 'Director'),
            'actor_dir': ('Actors', lambda x: x.get('cast', {}).values(), 'Actor')
        }
        self.movie_list = []
        if settings.REPORT_ENABLED:
            logger.create_report()

    def index(self):
        self.movie_list = []
        dict_index = self.get_dict_index()
        if settings.DUMP_INDEX_JSON_FILE_NAME:
            dump_to_json_file(dict_index)
        else:
            if settings.REMOTE_FILE_OPERATION_ENABLED:
                dict_apply(self.index_dir, dict_index, symlink_method=symlink)
            else:
                dict_apply(self.index_dir, dict_index)
        if settings.REPORT_ENABLED:
            insert_report(logger.finalize_report(), report_type='indexer')

    def get_dict_index(self):
        logger.info(u'****************************************')
        logger.info(u'**********      Indexer       **********')
        logger.info(u'****************************************')
        index_dict = defaultdict(dict)
        for folder in os.listdir(self.alphabetical_dir):
            folder = folder.decode('utf-8')
            logger.info(u'------ %s ------' % folder)
            folder_abs = os.path.join(self.alphabetical_dir, folder)
            if os.path.isdir(folder_abs):
                index_dict['Search'].update(
                    dict_merge_list_extend(index_dict['Search'], search_index((folder, folder_abs,))))
                matched = re.match('([^\(]*) \((\d{4})\).*', folder)
                if matched:
                    movie_name = matched.group(1)
                    year = matched.group(2)
                    found, movie = get_movie(movie_name, year)

                if movie and movie.imdb_id and not movie.indexed:
                    imdb_id = movie.imdb_id
                    imdb_data = self.mii_osdb.get_imdb_information(imdb_id)
                    if imdb_data:
                        logger.info(u'Found imdb data from opensubtitle:')
                        logger.debug(u'\tData: %s' % imdb_data)
                        for index_type, value in self.index_mapping.items():
                            new_index_for_movie = self.index_values(self.index_mapping[index_type][1](imdb_data),
                                                                    folder,
                                                                    folder_abs,
                                                                    index_type,
                                                                    movie=movie)
                            index_dict[value[0]].update(
                                dict_merge_list_extend(index_dict[value[0]], new_index_for_movie))
                    self.movie_list.append(movie)

        add_number_and_simplify(index_dict['Search'])
        remove_single_movie_person(index_dict)
        return index_dict

    def index_values(self, values, folder, folder_abs, index_type, movie=None):
        if values:
            index_dict = {}
            logger.info(u'\tIndexing %s, with %s' % (folder, values))
            try:
                for value in values:
                    if movie:
                        self.link_movie_value(movie, value, self.index_mapping[index_type][0])
                    value = value.strip()
                    if isinstance(value, float):
                        value = '%s' % int(value)
                    index_dict[value] = [(folder, folder_abs)]
            except Exception as e:
                logger.exception(u'\tFailed with exception :%s' % repr(e))
            return index_dict

    @staticmethod
    def link_movie_value(movie, value, link_type):
        if link_type == 'Genres':
            tag, created = Tag.objects.get_or_create(name=value)
            MovieTagging.objects.get_or_create(tag=tag, movie=movie)
        elif link_type == 'Years' and not movie.year:
            movie.year = value
        elif link_type == 'Ratings' and not movie.rating:
            movie.rating = value
        elif link_type in ['Actors', 'Directors']:
            person, _ = Person.objects.get_or_create(name=value)
            MovieRelation.objects.get_or_create(person=person, movie=movie, type=link_type)
            logger.debug(
                u'Link is saved :%s,%s,%s' % (smart_unicode(person.name), smart_unicode(movie.title), link_type))


def dump_to_json_file(index_dict):
    json_index = json.dumps(index_dict)
    json_index = json_index.replace(settings.LOCAL_ROOT, settings.NAS_ROOT)
    json_path = os.path.join(settings.DESTINATION_FOLDER, settings.DUMP_INDEX_JSON_FILE_NAME)
    if os.path.exists(json_path):
        os.remove(json_path)
    with open(json_path, 'w') as outfile:
        outfile.write(unicode(json_index))


def search_index(folder_and_folder_abs):
    matched = re.match('(^[^\(]*)\(.*', folder_and_folder_abs[0])
    if matched:
        name = matched.group(1)
    else:
        name = folder_and_folder_abs[0]
    return get_tree_from_list([x.upper() for x in name if x.isalpha()], folder_and_folder_abs)


def get_tree_from_list(remaining_letters, folder):
    if not remaining_letters:
        return {'--': [folder]}
    return {remaining_letters[0]: get_tree_from_list(remaining_letters[1:], folder),
            '--': [folder]}


def dict_merge_list_extend(d1, d2):
    try:
        for key, value in d2.items():
            if not d1.get(key):
                d1[key] = value
                continue
            if isinstance(d1.get(key), list):
                d1[key].extend(value)
            else:
                d1[key] = dict_merge_list_extend(d1[key], value)
    except AttributeError:
        pass
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
    for actor, value in index_dict['Actors'].items():
        if len(value) <= 1:
            del index_dict['Actors'][actor]
