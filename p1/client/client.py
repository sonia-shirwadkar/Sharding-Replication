# client.py
#!/usr/bin/env python

import os
import sys
import math
import socket
import json
import base64
import platform
import logging
from optparse import OptionParser
from common import *

FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.NOTSET)
logger = logging.getLogger(__name__)
logger.propagate = False

#Global data
NUM_SHARDS = 1
BUFFER_SIZE = 1024
FILESTORE = 'clientfilestore'
if (platform.system() == 'Linux'):
    PATH_SEP = '/'
elif (platform.system() == 'Windows'):
    PATH_SEP = '\\'

class Client(object):
    def __init__(self, configFile):
        self.configFile = configFile

    def connectToShards(self):
        self.server = []
        TCP_IP, TCP_PORT = parseConfigFile(configFile)
        logger.debug('IP:%s Port:%s', ''.join(str(e) + ' ' for e in TCP_IP), ''.join(str(e) + ' ' for e in TCP_PORT))

        try:
            for i in xrange(0, NUM_SHARDS):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server.append(sock)
                self.server[i].connect((TCP_IP[i], TCP_PORT[i]))
                print 'Connected to shard', i+1, 'at IP address:', TCP_IP[i], 'port', TCP_PORT[i]
                logger.info('Connected to shard %d at IP address: %s port:%s', i+1, TCP_IP[i], TCP_PORT[i])
        except:
            logger.error('Failed to open socket')
            raise

    def disconnectFromServer(self, server):
        print('Closing connection')
        req = Messages.disconnect
        server.sendall(json.dumps(req))
        server.close()
        print('Closed Connection')

    def queryShardCapacities(self):
        print 'Asking currently used storage'
        logger.info('Asking currently used storage')
        shardCapacity = []
        for i in xrange(0, NUM_SHARDS):
            capacity = 0
            req = Messages.bytestored
            req[Keys.BYTESTORED] = capacity
            try:
                self.server[i].sendall(json.dumps(req))
                reply = json.loads(self.server[i].recv(BUFFER_SIZE))
            except Exception as e:
                logger.info(str(e))
                raise
            logger.debug('Reply:%s', reply)
            shardCapacity.append(reply[Keys.BYTESTORED])
            logger.info('Reply was %s bytes', shardCapacity[i])
            print 'Reply was', shardCapacity[i], 'bytes'
        return shardCapacity

    def recalculateShardCapacities(self, shardCapacity, uploadFile):
        temp = 0
        totalCapacity = sum(shardCapacity)
        uploadSize = os.path.getsize(uploadFile)
        print 'Size of upload file', uploadSize, 'bytes'
        logger.info('Size of upload file %d bytes', uploadSize)
        try:
            if ((totalCapacity == 0) or (totalCapacity%NUM_SHARDS == 0)):
                for i in xrange(0, NUM_SHARDS):
                    if i == (NUM_SHARDS - 1):
                        temp = uploadSize - sum(shardCapacity[0:(NUM_SHARDS - 1)])
                    else:
                        temp = math.ceil(uploadSize / NUM_SHARDS)
                    shardCapacity[i] = int(temp)
            else:
                for i in xrange(0, NUM_SHARDS):
                    if i == (NUM_SHARDS - 1):
                        temp = uploadSize - sum(shardCapacity[0:(NUM_SHARDS - 1)])
                        print 'i=', i, 'temp=', temp
                    else:
                        temp = abs(shardCapacity[i] - math.ceil(totalCapacity / (NUM_SHARDS - i)))
                        print 'i=', i, 'temp=', temp
                        totalCapacity -= temp
                        print 'totalCapacity=', totalCapacity
                    shardCapacity[i] = int(temp)
                    print 'shardCapacity[i]=', shardCapacity[i]
        except Exception as e:
            logger.info(str(e))
            raise
        print 'Upload sizes are', shardCapacity
        logger.debug('Upload sizes are: %s', ''.join(str(e) + ' ' for e in shardCapacity))
        return shardCapacity

    def uploadFileToShards(self, shardCapacity, uploadFile):
        message = Messages.data
        message[Keys.FILENAME] = uploadFile
        try:
            fp = open(uploadFile, 'rb')
            for i in xrange(0, NUM_SHARDS):
                message[Keys.BYTESFROM] = fp.tell()
                data = fp.read(shardCapacity[i])
                if not data:
                    fp.close()
                    break
                end = fp.tell() - 1
                message[Keys.BYTESTO] = end
                print 'Uploading [', message[Keys.BYTESFROM], ',', message[Keys.BYTESTO], '] bytes'
                print 'Uploading', shardCapacity[i], 'bytes of', uploadFile, 'to shard', i+1
                data = EncoderDecoder.encodeData(data)
                message[Keys.DATA] = data
                self.server[i].sendall(json.dumps(message))
                print 'Done'
                self.disconnectFromServer(self.server[i])
        except Exception as e:
            logger.info(str(e))
            raise

    def queryShardsForDownloadFile(self, downloadFile):
        message = Messages.fileinfo
        message[Keys.FILENAME] = downloadFile
        metadata = []
        try:
            for i in xrange(0, NUM_SHARDS):
                print 'Asking if shard', i+1, 'has', downloadFile
                logger.info('Asking if shard%d has %s', i+1, downloadFile)
                self.server[i].sendall(json.dumps(message))
                temp = self.recvJSONMessage(self.server[i])
                metadata.append(temp)
                logger.info('Reply was %s', metadata[i])
                print 'Reply was [', temp[Keys.BYTESFROM], ',', temp[Keys.BYTESTO], '] of', temp[Keys.FILENAME]
        except Exception as e:
            logger.info(str(e))
            raise
        return metadata

    def downloadFile(self, metadata):
        data = ''
        try:
            for i in xrange(0, NUM_SHARDS):
                message = Messages.requestdata
                dict = metadata[i]
                #if (0 == message[Keys.BYTESFROM]):
                  #if (0 == message[Keys.BYTESTO]):
                    #print dict[Keys.FILENAME], 'not found on shard', i+1
                    #continue                
                message[Keys.FILENAME] = dict[Keys.FILENAME]
                message[Keys.BYTESFROM] = dict[Keys.BYTESFROM]
                message[Keys.BYTESTO] = dict[Keys.BYTESTO]
                self.server[i].sendall(json.dumps(message))

            data = ''
            filename = '.' + PATH_SEP + FILESTORE
            if not os.path.exists(filename):
                os.makedirs(filename)
            filename += PATH_SEP + message[Keys.FILENAME]
            for j in xrange(0, NUM_SHARDS):
                dict = metadata[j]
                if (dict[Keys.BYTESFROM] == 0 and dict[Keys.BYTESTO] == 0):
                    self.disconnectFromServer(self.server[j])
                    continue
                temp = self.recvJSONMessage(self.server[j])
                print 'Downloading [', temp[Keys.BYTESFROM], ',', temp[Keys.BYTESTO], '] of', temp[Keys.FILENAME], 'from shard', j+1
                data += EncoderDecoder.decodeData(temp[Keys.DATA])
                self.disconnectFromServer(self.server[j])
            if ('' !=  data):
                fp = open(filename, 'wb')
                fp.write(data)
                fp.close()
        except Exception as e:
            logger.info(str(e))
            raise

    def recvJSONMessage(self, server):
        data = ''
        while True:
            character = server.recv(1)
            data += character
            if character == '}':
                break
        return json.loads(data)


def parseConfigFile(configFile):
    print 'Reading configuration information from', configFile
    jsonData = []
    with open(configFile) as jsonFile:
        jsonData = json.load(jsonFile)
    TCP_IP = []
    TCP_PORT = []
    TCP_IP.append(jsonData["shard1ip"])
    TCP_PORT.append(int(jsonData["shard1port"]))
    TCP_IP.append(jsonData["shard2ip"])
    TCP_PORT.append(int(jsonData["shard2port"]))
    TCP_IP.append(jsonData["shard3ip"])
    TCP_PORT.append(int(jsonData["shard3port"]))
    return TCP_IP, TCP_PORT

def parseCommandLineArgs():
    try:
        parser = OptionParser(conflict_handler="resolve")
        parser.add_option("-c", "--config", type="string", help="Configuration file", dest="config")
        parser.add_option("-u", "--upload", type="string", help="File to upload", dest="upload")
        parser.add_option("-d", "--download", type="string", help="File to download", dest="download")
        (options, args) = parser.parse_args()
        configFile = options.config
        uploadFile = options.upload
        downloadFile = options.download
        logger.debug('Config:%s Upload:%s Download:%s', configFile, uploadFile, downloadFile)
    except:
        configFile = ''
        uploadFile = ''
        logger.debug('Error in parsing command line args')

    if uploadFile:
        return configFile, uploadFile, 1
    else:
        return configFile, downloadFile, 0

if __name__ == '__main__':
    configFile, dataFile, isUpload = parseCommandLineArgs()
    if isUpload:
        if (False == os.path.isfile(dataFile)):
            print 'File', dataFile,'does not exist'
            sys.exit(0)    
    
    client = Client(configFile)
    client.connectToShards()

    if isUpload:
        shardCapacity = client.queryShardCapacities()
        shardCapacity = client.recalculateShardCapacities(shardCapacity, dataFile)
        logger.info('Size of upload file is %s bytes', str(os.path.getsize(dataFile)))
        logger.info('Upload sizes are')
        for i in xrange(0, NUM_SHARDS):
            logger.info('shard%d %s bytes', i+1, shardCapacity[i])
        client.uploadFileToShards(shardCapacity, dataFile)
    else:
        metadata = client.queryShardsForDownloadFile(dataFile)
        client.downloadFile(metadata)


