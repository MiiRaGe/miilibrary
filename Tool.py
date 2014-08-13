import os,ConfigParser,logging,datetime
from movieinfo import theMovieDBWrapper,opensubtitleWrapper

#Create the directory @param(path) and return the path after creation [Error safe]
def makeDir(path):
    #Avoid the raise of IOError exception by checking if the directory exists first
    if not os.path.exists(path):
        os.makedirs(path)
    return path

#Remove a file [Error safe]
def remove(path):
    if os.path.exists(path):
        os.remove(path)

#Getting the configuration
Configuration = ConfigParser.SafeConfigParser()

#The setting file has to be present
if not os.path.exists("settings.cfg"):
    print("File Not found : settings.cfg")
    print("-> Please use settings-sample.cfg as a template")
    raise(IOError)

#Reading the whole configuration at initialisation time
Configuration.read("settings.cfg")

#Initialise Wrappers :
MovieDBWrapper = theMovieDBWrapper.TheMovieDBWrapper()
OpensubtitleWrapper = opensubtitleWrapper.OpensubtitleWrapper()

########### LOG #############
#To write the logs to
outputDir = Configuration.get('Global','outputFolder')

#Creating the log directory
outputDir = makeDir(os.path.join(outputDir,'log'))

#Creating the logger named 'NAS' and configuring
logger = logging.getLogger('NAS')

#Where it's written to
hdlr = logging.FileHandler(os.path.join(outputDir,'myNasLibrary.log.0'))
logger.addHandler(hdlr) 

#How it's formated in the logs
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)

#Amount of information in the tool
logger.setLevel(logging.DEBUG)

#Shift the logs file in order to have different runs of the script (0->1,1->2) etc...    
def shiftLog():
    #Removing the handler
    logger.removeHandler(hdlr) 
     
    #Timestamp for the logfile
    timestamp = datetime.datetime.now().strftime("%d-%m-%y.%H:%M")
    
    hdlr2 = logging.FileHandler(os.path.join(outputDir,'myNasLibrary' + timestamp + '.log'))
    #Readding the handler
    logger.addHandler(hdlr2)