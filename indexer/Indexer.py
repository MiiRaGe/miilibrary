import os,Tool,re,logging,platform
logger = logging.getLogger("NAS")

if platform.system() == 'Windows':
    import os

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
    def __init__(self,sourceDir):
        #All directory is always created by sorter and contains all movie sorted alphabetically
        self.sourceDir = sourceDir
        self.alphabeticalDir = os.path.join(sourceDir,"All")
        self.genreDir = Tool.make_dir(os.path.join(sourceDir,'Genres'))
        self.noGenreDir = Tool.make_dir(os.path.join(self.genreDir,'NOGENRE'))
        
    def index(self):
        imdbRegEx = re.compile('.IMDB_ID_(\d+)$')
        for folder in os.listdir(self.alphabeticalDir):
            folderAbs = os.path.join(self.alphabeticalDir,folder)
            if os.path.isdir(folderAbs):
                imdbFile = None
                for file in os.listdir(folderAbs):
                    id = imdbRegEx.match(file)
                    if id:
                        imdbFile = file
                        break   
                if imdbFile and not os.path.exists(os.path.join(folderAbs,imdbFile + '.indexed')):
                    imdbData = Tool.OpensubtitleWrapper.getImdbInformation(int(id.group(1)))
                    if imdbData:
                        logger.info(folder)
                        logger.info("\t" + str(imdbData.get('genres')))
                        genres = imdbData.get('genres')
                        if genres:
                            self.createGenreFolders(genres)
                            for genre in genres:
                                genre = genre.strip()
                                try:
                                    os.symlink(folderAbs,os.path.join(self.sourceDir,'Genres',genre,folder))
                                except:
                                    logger.debug("File already linked :" + folder + " in genre:" + genre)
                        else:
                            os.symlink(folderAbs,os.path.join(self.noGenreDir,folder))
                    else:
                        open(os.path.join(folderAbs,file + '.NO_IMDB_DATA'),'w')
                        os.symlink(folderAbs,os.path.join(self.noGenreDir,folder))
                    open(os.path.join(folderAbs,file + '.indexed'),'w')
                else:
                    open(os.path.join(folderAbs,file + '.NO_IMDB_FILE'),'w')
                    
    def createGenreFolders(self,genres):
        for genre in genres:
            genre = genre.strip()
            Tool.make_dir(os.path.join(self.sourceDir,'Genres',genre))
        


