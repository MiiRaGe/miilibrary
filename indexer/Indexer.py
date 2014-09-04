import logging
import platform
import re
import os

import tools

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
        #All directory is always created by sorter and contains all movie sorted alphabetically
        self.source_dir = source_dir
        self.alphabetical_dir = os.path.join(source_dir, "All")
        self.genre_dir = tools.make_dir(os.path.join(source_dir, 'Genres'))
        self.no_genre_dir = tools.make_dir(os.path.join(self.genre_dir, 'NOGENRE'))
        
    def index(self):
        #TODO : Add a method to destroy the index folders and rebuild them. (also removing .indexed)
        imdb_regex = re.compile('\.IMDB_ID_(?:tt)?(\d+)$')
        for folder in os.listdir(self.alphabetical_dir):
            folder_abs = os.path.join(self.alphabetical_dir, folder)
            if os.path.isdir(folder_abs):
                imdb_file = None
                id = None
                for file in os.listdir(folder_abs):
                    id = imdb_regex.match(file)
                    if id:
                        imdb_file = file
                        break

                if imdb_file:
                    if not os.path.exists(os.path.join(folder_abs, '%s.indexed' % imdb_file)):
                        imdb_data = tools.OpensubtitleWrapper.get_imdb_information(int(id.group(1)))
                        if imdb_data:
                            logger.info(folder)
                            logger.info("\t%s" % imdb_data.get('genres'))
                            logger.debug("\t%s" % imdb_data)
                            self.index_genre(imdb_data.get('genres'), folder, folder_abs)
                            #TODO: This is where new index using imdb_data should go following index_genre
                        else:
                            open(os.path.join(folder_abs, file + '.NO_IMDB_DATA'), 'w')
                            os.symlink(folder_abs, os.path.join(self.no_genre_dir, folder))
                        open(os.path.join(folder_abs, file + '.indexed'), 'w')
                    else:
                        logger.info("Folder already indexed :%s" % folder)
                else:
                    open(os.path.join(folder_abs, file + '.NO_IMDB_FILE'), 'w')
                    
    def create_genre_folders(self, genres):
        for genre in genres:
            genre = genre.strip()
            tools.make_dir(os.path.join(self.source_dir, 'Genres', genre))

    def index_genre(self, genres, folder, folder_abs):
        if genres:
            self.create_genre_folders(genres)
            for genre in genres:
                genre = genre.strip()
                try:
                    os.symlink(folder_abs, os.path.join(self.source_dir, 'Genres', genre, folder))
                except Exception, e:
                    logger.debug("File already linked : %s in genre: %s" % (folder, genre))
                    logger.exception("With exception :%s" % repr(e))
        else:
            os.symlink(folder_abs, os.path.join(self.no_genre_dir, folder))

