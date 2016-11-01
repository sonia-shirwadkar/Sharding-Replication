import threading
import json
import os
import logging
from common import *
from parsejson import *

FILESTORE = 'filestore'
logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.NOTSET)
logger.propagate = False

##################################################################
# Class:
#     ServerThread
# Description:
#     This class is is responsible for serving individual
#     client requests by creating threads.
#
##################################################################
class ServerThread(threading.Thread):
    def __init__(self, client, configFile):
        self.client = client
        self.configFile = configFile

    def createNewRequestThread(self):
        try:
            threading.Thread.__init__(self)
            t = threading.Thread(target=self.acceptClientRequests)
            t.daemon = True
            t.start()
        except Exception as e:
            logger.info(str(e))
            raise

    def acceptClientRequests(self):
        while (1):
            req = self.recvJSONMessage()
            if (MessageType.MSG_BYTESTORED in req.values()):
                self.sendShardCapacity()
            elif (MessageType.MSG_DISCONNECT in req.values()):
                return
            elif (MessageType.MSG_DATA in req.values()):
                self.saveFileUsingMetadata(req)
            elif (MessageType.MSG_FILEINFO in req.values()):
                metadata = self.readFileInfo(req[Keys.FILENAME])
                self.client.send(json.dumps(metadata))
            elif (MessageType.MSG_REQUESTDATA in req.values()):
                self.sendFileData(req)
            print 'Closed connection'

    def recvJSONMessage(self):
        try:
            data = ''
            while True:
                character = self.client.recv(1)
                data += character
                if character == '}':
                    break
        except Exception as e:
            logger.info(str(e))
            raise
        return json.loads(data)

    def sendShardCapacity(self):
        try:
            print 'Received status query from client'
            metadatafile = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + ServerConfigParser.getMetadataFile(self.configFile)
            capacity = getCapacityField(metadatafile)
            logger.info('reply is %d bytes', capacity)
            reply = Messages.bytestored
            reply[Keys.BYTESTORED] = capacity
            logger.info('Reply: %s', reply)
            self.client.sendall(json.dumps(reply))
        except Exception as e:
            logger.info(str(e))
            raise

    def sendFileData(self, metadata):
        try:
            filename = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + FILESTORE + PATH_SEP + metadata[Keys.FILENAME]
            if (False == os.path.isfile(filename)):
                print filename, 'not found'             
                return
            fp = open(filename, 'rb')
            data = fp.read()
            fp.close()
            message = Messages.data
            message[Keys.FILENAME] = metadata[Keys.FILENAME]
            message[Keys.BYTESFROM] = metadata[Keys.BYTESFROM]
            message[Keys.BYTESTO] = metadata[Keys.BYTESTO]
            message[Keys.DATA] = EncoderDecoder.encodeData(data)
            print 'Sending primary bytes for [', message[Keys.BYTESFROM], ',', message[Keys.BYTESTO], '] of', message[Keys.FILENAME]
            self.client.sendall(json.dumps(message))
        except Exception as e:
            logger.info(str(e))
            raise

    def saveFileUsingMetadata(self, data):
        try:
            print 'Received upload request of', int(int(data[Keys.BYTESTO]) - int(data[Keys.BYTESFROM])),'bytes for', data[Keys.FILENAME]
            print 'Received primary bytes [', data[Keys.BYTESFROM], ',', data[Keys.BYTESTO],'] for testfile.jpg'
            filedata = data[Keys.DATA]
            filedata = EncoderDecoder.decodeData(filedata)
            filename = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + FILESTORE
            if not os.path.exists(filename):
                os.makedirs(filename)
            filename += PATH_SEP + data[Keys.FILENAME]
            print 'Saving', data[Keys.FILENAME]
            with open(filename, 'wb') as f:
                f.write(filedata)
                f.close()
            metadata = Messages.fileinfo
            metadata[Keys.FILENAME] = data[Keys.FILENAME]
            metadata[Keys.BYTESFROM] = data[Keys.BYTESFROM]
            metadata[Keys.BYTESTO] = data[Keys.BYTESTO]
            self.writeFileInfo(metadata)
            newCapacity = long(metadata[Keys.BYTESTO]) - long(metadata[Keys.BYTESFROM])
            metadatafile = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + ServerConfigParser.getMetadataFile(self.configFile)
            addToShardCapacity(metadatafile, newCapacity)
        except Exception as e:
            logger.info(str(e))
            raise

    def writeFileInfo(self, metadata):
        try:
            metadatafile = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + ServerConfigParser.getMetadataFile(self.configFile)
            temp = readFileMetadata(metadatafile, metadata[Keys.FILENAME])
            if ({} == temp):
                deleteFileMetadata(metadatafile, metadata[Keys.FILENAME])
            addFileMetadata(metadatafile, metadata)
        except Exception as e:
            logger.info(str(e))
            raise

    def readFileInfo(self, filename):
        try:
            print 'Received download request for', filename        
            metadatafile = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + ServerConfigParser.getMetadataFile(self.configFile)
            metadata = readFileMetadata(metadatafile, filename)
            if (metadata == {}):
                metadata = Messages.fileinfo
                metadata[Keys.FILENAME] = filename
        except Exception as e:
            logger.info(str(e))
            raise
        print 'We have primary bytes for [', metadata[Keys.BYTESFROM], ',', metadata[Keys.BYTESTO], '] of', metadata[Keys.FILENAME]            
        return metadata