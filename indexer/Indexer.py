import logging
import platform
import re
import os

import tools

from middleware import mii_mongo


logger = logging.getLogger("NAS")

if platform.system() == 'Windows':
    __CSL = None

    def symlink(source, link_name):
        '''symlink(source, link_name)
           Creates a symbolic link pointing to source named link_name'''
        global __CSL
        if __CSL is None:
            import ctypes

            csl = ctypes.windll.kernel32.CreateSymbolicLinkW
            csl.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32)
            csl.restype = ctypes.c_ubyte
            __CSL = csl
        flags = 0
        if source is not None and os.path.isdir(source):
            flags = 1
        if __CSL(link_name, source, flags) == 0:
            raise ctypes.WinError()

    os.symlink = symlink


class Indexer:
    def __init__(self, source_dir):
        # All directory is always created by sorter and contains all movie sorted alphabetically
        self.mii_osdb = mii_mongo.MiiOpenSubtitleDB()
        self.source_dir = source_dir
        self.alphabetical_dir = os.path.join(source_dir, "All")
        self.search_dir = os.path.join(source_dir, "Search")
        self.index_mapping = {
            'genre_dir': (os.path.join(source_dir, 'Genres'), lambda x: x.get('genres')),
            'rating_dir': (os.path.join(source_dir, 'Ratings'), lambda x: [str(int(float(x.get('rating'))))]),
            'year_dir': (os.path.join(source_dir, 'Years'), lambda x: [x.get('year')]),
            'director_dir': (os.path.join(source_dir, 'Directors'), lambda x: x.get('directors', {}).values()),
            'actor_dir': (os.path.join(source_dir, 'Actors'), lambda x: x.get('cast', {}).values())
        }

    def init(self):
        for folder, _ in self.index_mapping.values() + [(self.search_dir, None)]:
            tools.delete_dir(folder)
            tools.make_dir(folder)

    def index(self):
        logger.info("****************************************")
        logger.info("**********      Indexer       **********")
        logger.info("****************************************")
        self.init()

        imdb_regex = re.compile('\.IMDB_ID_(?:tt)?(\d+)$')
        for folder in os.listdir(self.alphabetical_dir):
            logger.info('------ %s ------' % folder)
            folder_abs = os.path.join(self.alphabetical_dir, folder)
            if os.path.isdir(folder_abs):
                imdb_file = None
                id = None
                for file in os.listdir(folder_abs):
                    id = imdb_regex.match(file)
                    if id:
                        imdb_file = file
                        break
                self.search_index(folder_abs, folder)

                if imdb_file:
                    logger.info('Found imdb file %s' % imdb_file)
                    imdb_data = self.mii_osdb.get_imdb_information(int(id.group(1)))
                    if imdb_data:
                        logger.info('Found imdb data from opensubtitle:')
                        logger.debug("\tData: %s" % imdb_data)
                        for index in self.index_mapping.keys():
                            self.index_values(self.index_mapping[index][1](imdb_data), folder, folder_abs, index)
                    else:
                        # FIXME: Probably need to remove that, not sure what it's for
                        open(os.path.join(folder_abs, file + '.NO_IMDB_DATA'), 'w')
                else:
                    open(os.path.join(folder_abs, '.NO_IMDB_FILE'), 'w')

        self.add_counting(self.search_dir, skipped=True)

    def index_values(self, values, folder, folder_abs, index_dir):
        if values:
            logger.info('\tIndexing %s, with %s' % (folder, values))
            try:
                for value in values:
                    value = value.strip()
                    tools.make_dir(os.path.join(self.index_mapping[index_dir][0], value))
                    os.symlink(folder_abs, os.path.join(self.index_mapping[index_dir][0], value, folder))
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
            count = self._add_counting(current_folder)

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

    def search_index(self, folder_abs, folder):
        current_path = []
        matched = re.match('(^[^\(]*)\(.*', folder)
        if matched:
            name = matched.group(1)
        else:
            name = folder
        for letters in [x.upper() for x in name if x.isalpha()]:
            current_path += letters
            letter_folder = tools.make_dir(os.path.join(self.search_dir, *current_path))
            result_folder = tools.make_dir(os.path.join(letter_folder, '--'))
            os.symlink(folder_abs, os.path.join(result_folder, folder))

