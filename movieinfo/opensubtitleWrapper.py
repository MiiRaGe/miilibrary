'''
Created on 26 janv. 2014

@author: MiiRaGe
'''

from xmlrpclib import ProtocolError,ServerProxy
import time,logging
import Tool

class OpensubtitleWrapper:
    
    def __init__(self):
        self.logger = logging.getLogger("NAS")
        self.server = ServerProxy("http://api.opensubtitles.org/xml-rpc")
        self.loginSuccessfull = False
            
    
    def logIn(self,retry = False,maxtry = 10):
        status = '503'
        result = None
        goOn = True
        failCount = 0
        while (goOn):
            try:
                self.logger.info("Login into openSubtitle...")
                username = Tool.Configuration.get('OpenSubtitle','login')
                password = Tool.Configuration.get('OpenSubtitle','password')
                result = self.server.LogIn(username,password,"gb","miinaslibraryUA")
                self.token = result.get("token")
                status = result.get("status")
                if status.startswith('200'):
                    self.loginSuccessfull = True
                    return
            except (ProtocolError):
                self.logger.debug("Response : " + str(result))
                self.logger.info("Got rejected by the API, waiting 1minutes")
            failCount += 1
            if not retry or failCount == maxtry:
                self.loginSuccessfull = False
                return
            else:
                time.sleep(60)
            
    def getImdbInformation(self,id):
        if not self.loginSuccessfull :
            self.logIn()
            if not self.loginSuccessfull :
                return ''    
        time.sleep(0.3)
        result = ''
        while True:
            try :
                result =  self.server.GetIMDBMovieDetails(self.token, id)
                return result.get("data")
            except (ProtocolError):
                self.logger.info("Result :" + str(result))
                self.logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)
            
        
          
    def getMovieNames(self,movieHashes):
        if not self.loginSuccessfull :
            self.logIn()
            if not self.loginSuccessfull :
                return ''
        return self.server.CheckMovieHash(self.token, movieHashes).get("data")
    
    def getMovieNames2(self,movieHashes):
        if not self.loginSuccessfull :
            self.logIn(True,10)
            if not self.loginSuccessfull :
                return ''
        time.sleep(0.3)
        result = ''
        while True:
            try :
                result =  self.server.CheckMovieHash2(self.token, movieHashes)
                return result.get("data")
            except (ProtocolError):
                self.logger.info("Result :" + str(result))
                self.logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)
    
    def getSubtitles(self,movieHash,movieSize,movieName):
        if not self.loginSuccessfull :
            self.logIn()
            if not self.loginSuccessfull :
                return ''
        time.sleep(0.3)
        result = None
        while True:
            try :
                result =  self.server.SearchSubtitles(self.token,[{"moviehash":movieHash,"moviebytesize":movieSize,"query":movieName}],{"limit":100})
                self.logger.debug(result)
                result = result.get("data")
                return result
            except (ProtocolError):
                self.logger.info("Result :" + str(result))
                self.logger.info("Got rejected by the API, waiting 1minutes")
                time.sleep(60)
    
    def exit(self):
        return self.server.LogOut()