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
import copy
from operator import itemgetter

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

class Client(object):
    def __init__(self, configFile):
        self.configFile = configFile
        self.numShards = NUM_SHARDS

    def connectToShards(self):
        count  = 0
        self.server = []
        TCP_IP, TCP_PORT = parseConfigFile(self.configFile)
        print TCP_IP
        print TCP_PORT
        logger.debug('IP:%s Port:%s', ''.join(str(e) + ' ' for e in TCP_IP), ''.join(str(e) + ' ' for e in TCP_PORT))
        try:
            for i in xrange(0, self.numShards):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect((TCP_IP[i], TCP_PORT[i]))
                    self.server.append(sock)
                    count = count + 1
                    print 'Connected to shard', i+1, 'at IP address:', TCP_IP[i], 'port', TCP_PORT[i]
                    logger.info('Connected to shard %d at IP address: %s port:%s', i+1, TCP_IP[i], TCP_PORT[i])
                except:
                    logger.info('Could not connect to shard %d at IP address: %s port:%s', i + 1, TCP_IP[i], TCP_PORT[i])
                    continue
        except:
            logger.error('Failed to open socket')
            raise
        self.numShards = count

    # def disconnectFromServer(self, server):
    #     print('Closing connection')
    #     req = Messages.disconnect
    #     server.sendall(json.dumps(req))
    #     server.close()
    #     print('Closed Connection')

    def queryShardCapacities(self):
        print 'Asking currently used storage'
        logger.info('Asking currently used storage')
        shardCapacity = []
        for i in xrange(0, self.numShards):
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
        count = self.numShards
        indexList = [i[0] for i in sorted(enumerate(shardCapacity), key=lambda x:x[1])]
        sortedShardCapacity = copy.deepcopy(sorted(shardCapacity, reverse=True))
        uploadSize = os.path.getsize(uploadFile)
        totalCapacity = sum(sortedShardCapacity) + uploadSize
        sizePerShard = totalCapacity / self.numShards
        remainder = totalCapacity % self.numShards
        for i in xrange (0, self.numShards):
            if (sortedShardCapacity[i] >= sizePerShard):
                count = count - 1
                totalCapacity -= sortedShardCapacity[i]
                remainder = totalCapacity % count
                sizePerShard = totalCapacity / count
                sortedShardCapacity[i] = 0
            else:
                sortedShardCapacity[i] = sizePerShard - sortedShardCapacity[i] + remainder
                remainder = 0
        for i in xrange(0, len(indexList)):
            shardCapacity[i] = sortedShardCapacity[indexList.index(i)]
        return shardCapacity

    def uploadFileToShards(self, shardCapacity, uploadFile):
        message = Messages.data
        message[Keys.FILENAME] = uploadFile
        # message[Keys.FILESIZE] = os.path.getsize(uploadFile)
        try:
            fp = open(uploadFile, 'rb')
            for i in xrange(0, self.numShards):
                if (shardCapacity[i] == 0):
                    continue
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
                # self.disconnectFromServer(self.server[i])
        except Exception as e:
            logger.info(str(e))
            raise

    def queryShardsForDownloadFile(self, downloadFile):
        message = Messages.fileinfo
        message[Keys.FILENAME] = downloadFile
        metadata = []
        try:
            for i in xrange(0, self.numShards):
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

    def sendRequestDataMessageToShards(self, metadata):
        try:
            for i in xrange(0, self.numShards):
                message = Messages.requestdata
                dict = metadata[i]
                if (0 == dict[Keys.BYTESFROM] and 0 == dict[Keys.BYTESTO]):
                  print dict[Keys.FILENAME], 'not found on shard', i+1
                  continue
                message[Keys.FILENAME] = dict[Keys.FILENAME]
                message[Keys.BYTESFROM] = dict[Keys.BYTESFROM]
                message[Keys.BYTESTO] = dict[Keys.BYTESTO]
                self.server[i].sendall(json.dumps(message))
        except Exception as e:
            logger.info(str(e))
            raise

    def downloadFile(self, metadata):
        try:
            self.sendRequestDataMessageToShards(metadata)
            data = ''
            for j in xrange(0, self.numShards):
                dict = metadata[j]
                if (dict[Keys.BYTESFROM] == 0 and dict[Keys.BYTESTO] == 0):
                    continue
                temp = self.recvJSONMessage(self.server[j])
                if (0 == temp[Keys.BYTESFROM] and 0 == temp[Keys.BYTESTO]):
                    continue
                print 'Downloading [', temp[Keys.BYTESFROM], ',', temp[Keys.BYTESTO], '] of', temp[Keys.FILENAME], 'from shard', j+1
                data += EncoderDecoder.decodeData(temp[Keys.DATA])
            filename = '.' + PATH_SEP + FILESTORE
            if not os.path.exists(filename):
                os.makedirs(filename)
            message = metadata[0]
            filename += PATH_SEP + message[Keys.FILENAME]
            if ('' !=  data):
                fp = open(filename, 'wb')
                fp.write(data)
                fp.close()
        except Exception as e:
            logger.info(str(e))
            raise

    def downloadBackupData(self, metadata):
        i = 0
        tupleList = self.calculateBackupRequestOrder(metadata)
        data = ''
        filename = '.' + PATH_SEP + FILESTORE
        if not os.path.exists(filename):
            os.makedirs(filename)
        filename += PATH_SEP + tupleList[0][0][Keys.FILENAME]
        if (os.path.isfile(filename)):
            os.remove(filename)
        try:
            for tuple in tupleList:
                self.server[int(tuple[1])].sendall(json.dumps(tuple[0]))
                dict = tuple[0]
                if (dict[Keys.BYTESFROM] == 0 and dict[Keys.BYTESTO] == 0):
                    continue
                temp = self.recvJSONMessage(self.server[tuple[1]])
                print 'Downloading [', temp[Keys.BYTESFROM], ',', temp[Keys.BYTESTO], '] of', temp[Keys.FILENAME], 'from shard', i+1
                if ('' != temp[Keys.DATA]):
                    fp = open(filename, 'ab')
                    fp.write(EncoderDecoder.decodeData(temp[Keys.DATA]))
                    fp.close()
                i += 1
        except Exception as e:
            logger.info(str(e))
            raise

    def getFileSizeFromMetadata(self, metadata):
        fileSize = 0
        temp = 0
        for i in xrange(0, len(metadata)):
            dict = metadata[i]
            temp = max(dict[Keys.BYTESTO], dict[Keys.BYTESTO2], dict[Keys.BYTESTO3])
            if (temp > fileSize):
                fileSize = temp
        return fileSize

    def calculateBackupRequestOrder(self, metadata):
        newList = []
        fileSize = self.getFileSizeFromMetadata(metadata)
        for i in xrange(0, len(metadata)):
            dict = metadata[i]
            message = copy.deepcopy(Messages.requestdata)
            message[Keys.FILENAME] = dict[Keys.FILENAME]
            message[Keys.BYTESFROM] = dict[Keys.BYTESFROM]
            message[Keys.BYTESTO] = dict[Keys.BYTESTO]
            temp = ()
            temp += (message,)
            temp += (i,)
            newList.append(temp)
        shardNumber = 0
        requiredfrom = 0
        requiredto = 0
        sortedlist = sorted(metadata, key=itemgetter(Keys.BYTESFROM))
        shard1 = sortedlist[0]
        shard2 = sortedlist[1]
        if (shard1[Keys.BYTESFROM] != 0):   #shard1 down
            requiredfrom = 0
            requiredto = shard1[Keys.BYTESFROM] - 1
        elif ((shard1[Keys.BYTESTO] + 1) != shard2[Keys.BYTESFROM]): #shard2 down
            requiredfrom = shard1[Keys.BYTESTO] + 1
            requiredto = shard2[Keys.BYTESFROM] - 1
        else: #shard3 down
            requiredfrom = shard2[Keys.BYTESTO] + 1
            requiredto = fileSize
            # requiredto = shard2[Keys.FILESIZE] - 1
        print 'Shard down, bytes missing: [', requiredfrom, ',', requiredto, ']'
        bytesfrom =requiredfrom
        bytesto = requiredto
        numBytes = requiredto + requiredfrom
        distribution = []
        for i in xrange (0, self.numShards):
            tup = ()
            tup += (requiredfrom,)
            if (i == self.numShards-1):
                tup += (requiredto,)
            else:
                tup += (long(numBytes/self.numShards),)
            distribution.append(tup)
            temp = distribution[-1]
            requiredfrom = temp[1] + 1
        #print 'Distribution:', distribution
        index = 0
        for i in xrange(0, len(sortedlist)):
            item = metadata[i]
            #print 'item', item
            message = copy.deepcopy(Messages.requestdata)
            message[Keys.FILENAME] = item[Keys.FILENAME]
            temp = ()
            temp += (item[Keys.BYTESFROM2],)
            temp += (item[Keys.BYTESTO2],)
            #print 'temp1:', temp
            if (temp in distribution):
                message[Keys.BYTESFROM] = item[Keys.BYTESFROM2]
                message[Keys.BYTESTO] = item[Keys.BYTESTO2]
                tup = ()
                tup += (message,)
                tup += (shardNumber,)
                newList.append(tup)
                distribution.remove(temp)
            temp = ()
            temp += (item[Keys.BYTESFROM3],)
            temp += (item[Keys.BYTESTO3],)
            #print 'temp2:', temp
            if (temp in distribution):
                message[Keys.BYTESFROM] = item[Keys.BYTESFROM3]
                message[Keys.BYTESTO] = item[Keys.BYTESTO3]
                tup = ()
                tup += (message,)
                tup += (shardNumber,)
                newList.append(tup)
                distribution.remove(temp)
            shardNumber += 1
        newList = sorted(newList, key=lambda tup: tup[0][Keys.BYTESFROM])
        # print newList
        return newList

    def recvJSONMessage(self, server):
        data = ''
        while True:
            character = server.recv(1)
            data += character
            if character == '}':
                break
        return json.loads(data)

    def printTimestamps(self):
        message = Messages.timestamp
        for i in xrange (0, self.numShards):
            self.server[i].sendall(json.dumps(message))
            ts = json.dumps(self.server[i].recv(BUFFER_SIZE))
            print 'TIMESTAMP', i, ':', ts
			
if __name__ == '__main__':
    from common import *
    BUFFER_SIZE = 1024
    FILESTORE = 'clientfilestore'
    if (platform.system() == 'Linux'):
        PATH_SEP = '/'
    elif (platform.system() == 'Windows'):
        PATH_SEP = '\\'
    NUM_SHARDS = 3
    FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.NOTSET)
    logger = logging.getLogger(__name__)
    logger.propagate = False

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
        client.uploadFileToShards(shardCapacity, dataFile)
    else:
        metadata = client.queryShardsForDownloadFile(dataFile)
        if (len(metadata) < NUM_SHARDS):
            client.downloadBackupData(metadata)
        else:
            client.downloadFile(metadata)
	
	#client.printTimestamps()


