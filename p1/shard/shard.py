# shard.py
#!/usr/bin/env python

import logging
import os
import socket
import threading
import json
from common import *
from optparse import OptionParser
from serverthread import *

# SIZE_RECV_MSG = 256
FILESTORE = 'filestore'
logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.NOTSET)
logger.propagate = False

##################################################################
# Class:
#     Server
# Description:
#     This class is the main engine for the shard.
#     Methods of this class will be responsible for serving
#     client
##################################################################
# class Server(threading.Thread):
class Server(object):
    def __init__(self, configFile):
        #
        # TODO: THE FOLLOWING LINE IS ONLY FOR TEST
        # TODO: REPLACE WITH socket.gethostname()
        #
        self.configFile = configFile
        self.ip = socket.gethostname()
        self.port = int(ServerConfigParser.getListenPort(configFile))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        logger.debug('IP:%s Port:%s', self.ip, self.port)
        logger.info('listening on port: %s', self.port)
        print 'Listening on port', self.port
        self.socket.listen(5)

    def accept_connection(self):
        self.newconn, self.newaddress = self.socket.accept()
        return self.newconn, self.newaddress

    def is_connected(self):
        return True if not self.conn else False

##################################################################

def parseCommandLineArgs():
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-c", "--config", type="string", help="Configuration file", dest="config")
    (options, args) = parser.parse_args()
    configFile = options.config
    return configFile

if __name__ == '__main__':
    configFile = parseCommandLineArgs()
    server = Server(configFile)
    while True:
        logger.info('*** waiting for requests ***\n')
        print ('*** waiting for requests ***\n')
        (client, addr) = server.accept_connection()
        threadObject = ServerThread(client, configFile)
        clientThread = threadObject.createNewRequestThread()
