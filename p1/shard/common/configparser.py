import json
from common import *

##################################################################
# Class:
#     ConfigParser
# Description:
#     This class is responsible for parsing JSON configuration files
#
##################################################################
class ConfigParser:
    @classmethod
    def getHomedir(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_HOMEDIR]

    @classmethod
    def getMetadataFile(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_METADATAFILE]

    @classmethod
    def getShard1IP(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD1IP]

    @classmethod
    def getShard1Port(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD1PORT]

    @classmethod
    def getShard2IP(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD2IP]

    @classmethod
    def getShard2Port(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD2PORT]


##################################################################
# Class:
#     ServerConfigParser
# Description:
#     This class is responsible for parsing JSON configuration files
#     It inherits ConfigParser as well as provides functions to parse
#     server specific fields
#
##################################################################
class ServerConfigParser(ConfigParser):
    @classmethod
    def getListenPort(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_LISTENPORT]

##################################################################
# Class:
#     ClientConfigParser
# Description:
#     This class is responsible for parsing JSON configuration files
#     It inherits ConfigParser as well as provides functions to parse
#     client specific fields
#
##################################################################
class ClientConfigParser(ConfigParser):
    @classmethod
    def getShard3IP(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD3IP]

    @classmethod
    def getShard3Port(self, configFile):
        try:
            configData = []
            with open(configFile) as jsonFile:
                configData = json.load(jsonFile)
        except:
            raise
        return configData[Config.CONF_SHARD3PORT]