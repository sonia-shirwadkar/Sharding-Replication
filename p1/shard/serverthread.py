import threading
import sys
import json
import os
import errno
import select
import socket
import logging
import time
import datetime
from common import *
from parsejson import *

FILESTORE = 'filestore'
logger = logging.getLogger(__name__)
FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
# logger.propagate = False

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
        self.NUM_BACKUP_SHARDS = 2
        self.client = client
        self.configFile = configFile
        self.metadatafile = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + ServerConfigParser.getMetadataFile(configFile)

    def createNewRequestThread(self):
        try:
            threading.Thread.__init__(self)
            t = threading.Thread(target=self.acceptClientRequests)
            t.daemon = True
            t.start()
        except Exception as e:
            logger.info(str(e))
            raise

    def sendDateTimeToClient(self):
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        logger.info('Timestamp: %s', st)
        message = Messages.timestamp
        message[Keys.TIMESTAMP] = st
        self.client.sendall(json.dumps(message))
			
    def acceptClientRequests(self):
        while (1):
            req = self.recvJSONMessage(self.client)
            if (MessageType.MSG_BYTESTORED in req.values()):
                self.sendShardCapacity()
            elif (MessageType.MSG_DATA in req.values()):
                print 'Data received from client'
                self.saveFileUsingMetadata(req)
            elif (MessageType.MSG_FILEINFO in req.values()):
                print 'Received download request for', req[Keys.FILENAME]
                metadata = self.getFileInfo(req[Keys.FILENAME])
                print 'We have primary bytes for [', metadata[Keys.BYTESFROM], ',', metadata[Keys.BYTESTO], '] of', metadata[Keys.FILENAME]
                self.client.send(json.dumps(metadata))
            elif (MessageType.MSG_REQUESTDATA in req.values()):
                self.sendFileData(req)
            elif (MessageType.MSG_BACKUPDATA in req.values()):
                self.receiveBackupData(req)
            elif (MessageType.MSG_TIMESTAMP in req.values()):
                self.sendDateTimeToClient()				

    def recvJSONMessage(self, jsonsocket):
        try:
            data = ''
            while True:
                character = jsonsocket.recv(1)
                data += character
                if character == '}':
                    break
        except Exception as e:
            logger.info(str(e))
            raise
        return json.loads(data)

    def sendShardCapacity(self):
        metadatafile = ServerConfigParser.getMetadataFile(self.configFile)
        capacity = getCapacity(metadatafile)
        try:
            reply = Messages.bytestored
            reply[Keys.BYTESTORED] = capacity
            logger.info('Reply: %s', reply)
            self.client.sendall(json.dumps(reply))
        except Exception as e:
            logger.debug(str(e))
            raise

    def sendFileData(self, metadata):
        try:
            filemetadata = self.getFileMetadata(metadata[Keys.FILENAME])
            if ({} == filemetadata):
                message = Messages.data
                message[Keys.FILENAME] = metadata[Keys.FILENAME]
                self.client.sendall(json.dumps(message))
                print 'File', message[Keys.FILENAME], 'not found'
                return
            filename = filemetadata[Keys.FILENAME]
            if((filemetadata[Keys.BYTESFROM2] == metadata[Keys.BYTESFROM]) and (filemetadata[Keys.BYTESTO2] == metadata[Keys.BYTESTO])):
                filename = filemetadata[Keys.FILENAME2]
            elif((filemetadata[Keys.BYTESFROM3] == metadata[Keys.BYTESFROM]) and (filemetadata[Keys.BYTESTO3] == metadata[Keys.BYTESTO])):
                filename = filemetadata[Keys.FILENAME3]
            path = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + FILESTORE + PATH_SEP + filename
            if (False == os.path.isfile(path)):
                print path, 'not found'
                return
            fp = open(path, 'rb')
            data = fp.read()
            fp.close()
            message = Messages.data
            message[Keys.FILENAME] = metadata[Keys.FILENAME]
            # message[Keys.FILESIZE] = filemetadata[Keys.FILESIZE]
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
            metadatafile = ServerConfigParser.getMetadataFile(self.configFile)
            print 'Received upload request of', int(int(data[Keys.BYTESTO]) - int(data[Keys.BYTESFROM])),'bytes for', data[Keys.FILENAME]
            print 'Received primary bytes [', data[Keys.BYTESFROM], ',', data[Keys.BYTESTO],'] for', data[Keys.FILENAME]
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
            metadata = self.getFileMetadata(data[Keys.FILENAME])
            if ({} == metadata):
                metadata = Messages.metadata
            else:
                capacity = getCapacity(metadatafile)
                capacity = capacity - (metadata[Keys.BYTESTO] - metadata[Keys.BYTESFROM] - 1)
                setCapacity(metadatafile, capacity)
            metadata[Keys.FILENAME] = data[Keys.FILENAME]
            # metadata[Keys.FILESIZE] = data[Keys.FILESIZE]
            metadata[Keys.BYTESFROM] = data[Keys.BYTESFROM]
            metadata[Keys.BYTESTO] = data[Keys.BYTESTO]
            capacity = 0
            capacity = getCapacity(metadatafile)
            capacity = capacity + (metadata[Keys.BYTESTO] - metadata[Keys.BYTESFROM] + 1)
            setCapacity(metadatafile, capacity)
            self.setFileMetadata(metadata)
            replica = self.sendBackupData(data)
        except Exception as e:
            logger.info(str(e))
            raise

    def sendBackupData(self, data):
        metadata = self.divideDataForShards(data)
        backupShards = self.connectToBackupShards()
        numBytes = long(data[Keys.BYTESTO]) - long(data[Keys.BYTESFROM])
        datastr = EncoderDecoder.decodeData(data[Keys.DATA])
        try:
            bytesfrom = 0
            if (0 == self.NUM_BACKUP_SHARDS):
                bytesto = long(numBytes)
            else:
                bytesto = long(numBytes / self.NUM_BACKUP_SHARDS)
            for i in xrange (0, self.NUM_BACKUP_SHARDS):
                keyfrom = Keys.BYTESFROM + str(i+2)
                keyto = Keys.BYTESTO + str(i+2)
                backupdata = {}
                backupdata = Messages.backupdata
                backupdata[Keys.FILENAME] = data[Keys.FILENAME]
                # backupdata[Keys.FILESIZE] = data[Keys.FILESIZE]
                backupdata[Keys.BYTESFROM] = metadata[keyfrom]
                backupdata[Keys.BYTESTO] = metadata[keyto]
                backupdata[Keys.DATA] = EncoderDecoder.encodeData(datastr[bytesfrom:(bytesto+1)])
                print 'Sending backup bytes [', backupdata[Keys.BYTESFROM], backupdata[Keys.BYTESTO], '] to shard', i+1
                bytesfrom = bytesto + 1
                if (i == self.NUM_BACKUP_SHARDS-1):
                    bytesto = data[Keys.BYTESTO]
                else:
                    bytesto += bytesfrom
                backupShards[i].sendall(json.dumps(backupdata))
        except Exception as e:
            logger.info(sys.exc_info())
            raise
        return metadata

    def setFileMetadata(self, metadata):
        try:
            addFileMetadata(self.metadatafile, metadata)
        except Exception as e:
            logger.info(str(e))
            raise

    def getFileInfo(self, filename):
        try:
            metadata = self.getFileMetadata(filename)
            if ({} == metadata):
                message = Messages.fileinfo
                message[Keys.FILENAME] = filename
                return message
            message = Messages.fileinfo
            message[Keys.FILENAME] = filename
            # message[Keys.FILESIZE] = metadata[Keys.FILESIZE]
            message[Keys.BYTESFROM] = metadata[Keys.BYTESFROM]
            message[Keys.BYTESTO] = metadata[Keys.BYTESTO]
            message[Keys.BYTESFROM2] = metadata[Keys.BYTESFROM2]
            message[Keys.BYTESTO2] = metadata[Keys.BYTESTO2]
            message[Keys.BYTESFROM3] = metadata[Keys.BYTESFROM3]
            message[Keys.BYTESTO3] = metadata[Keys.BYTESTO3]
        except Exception as e:
            logger.info(str(e))
            raise
        return message

    def getFileMetadata(self, filename):
        try:
            metadata = readFileMetadata(self.metadatafile, filename)
        except Exception as e:
            logger.info(str(e))
            raise
        return metadata

    # def setFileSizeInMetaData(self, filename):
    #     metadata = self.getFileMetadata(filename)
    #     filesize = max(metadata[Keys.BYTESTO], metadata[Keys.BYTESTO2], metadata[Keys.BYTESTO3])
    #     metadata[Keys.FILESIZE] = filesize
    #     self.setFileMetadata(metadata)
    #     return filesize

    def receiveBackupData(self, metadata):
        print 'Received backup data bytes [', metadata[Keys.BYTESFROM], ',', metadata[Keys.BYTESTO], ']'
        if (0 == metadata[Keys.BYTESFROM] and 0 == metadata[Keys.BYTESTO]):
            logger.debug('Invalid data received')
            return
        metadatafile = ServerConfigParser.getMetadataFile(self.configFile)
        capacity = getCapacity(metadatafile)
        capacity = capacity + (metadata[Keys.BYTESTO] - metadata[Keys.BYTESFROM] + 1)
        setCapacity(metadatafile, capacity)
        filedir = ServerConfigParser.getHomedir(self.configFile) + PATH_SEP + FILESTORE
        if not os.path.exists(filedir):
            os.makedirs(filedir)
        filename = metadata[Keys.FILENAME] + str(1)
        path = filedir + PATH_SEP + filename
        if (True == os.path.isfile(path)):
            filename = metadata[Keys.FILENAME] + str(2)
            path = filedir + PATH_SEP + filename
        with open(path, 'wb') as f:
            f.write(EncoderDecoder.decodeData(metadata[Keys.DATA]))
            f.close()
        filemetadata = self.getFileMetadata(metadata[Keys.FILENAME])
        if ({} == filemetadata):
            filemetadata = Messages.metadata
            filemetadata[Keys.FILENAME] = metadata[Keys.FILENAME]
            # filemetadata[Keys.FILESIZE] = metadata[Keys.FILESIZE]
        if (filemetadata[Keys.FILENAME2] == ''):
            filemetadata[Keys.FILENAME2] = filename
            filemetadata[Keys.BYTESFROM2] = metadata[Keys.BYTESFROM]
            filemetadata[Keys.BYTESTO2] = metadata[Keys.BYTESTO]
        else:
            filemetadata[Keys.FILENAME3] = filename
            filemetadata[Keys.BYTESFROM3] = metadata[Keys.BYTESFROM]
            filemetadata[Keys.BYTESTO3] = metadata[Keys.BYTESTO]
        self.setFileMetadata(filemetadata)
        # filesize = self.setFileSizeInMetaData(metadata[Keys.FILENAME])
        # print 'Total filesize:', filesize

    def divideDataForShards(self, data):
        numBytes = long(data[Keys.BYTESTO]) + long(data[Keys.BYTESFROM])
        metadata = Messages.fileinfo
        metadata[Keys.FILENAME] = data[Keys.FILENAME]
        # metadata[Keys.FILESIZE] = data[Keys.FILESIZE]
        metadata[Keys.BYTESFROM] = data[Keys.BYTESFROM]
        metadata[Keys.BYTESTO] = data[Keys.BYTESTO]
        if (0 == self.NUM_BACKUP_SHARDS):
            return metadata
        bytesfrom = data[Keys.BYTESFROM]
        for i in xrange (0, self.NUM_BACKUP_SHARDS):
            keyfrom = Keys.BYTESFROM + str(i+2)
            keyto = Keys.BYTESTO + str(i+2)
            metadata[keyfrom] = bytesfrom
            if (i == self.NUM_BACKUP_SHARDS-1):
                metadata[keyto] = data[Keys.BYTESTO]
            else:
                metadata[keyto] = long(numBytes/self.NUM_BACKUP_SHARDS)
            bytesfrom = metadata[keyto] + 1
        return metadata

    def connectToBackupShards(self):
        backupServers = []
        count = 0
        TCP_IP, TCP_PORT = self.getBackupShardConfigInfo()
        logger.debug('IP:%s Port:%s', ''.join(str(e) + ' ' for e in TCP_IP), ''.join(str(e) + ' ' for e in TCP_PORT))
        self.numBackupShards = len(TCP_IP);

        try:
            for i in xrange(0, self.NUM_BACKUP_SHARDS):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                try:
                    sock.connect((TCP_IP[i], TCP_PORT[i]))
                    sock.setblocking(0)
                    count = count + 1
                    backupServers.append(sock)
                    logger.info('Connected to shard %d at IP address: %s port:%s', i + 1, TCP_IP[i], TCP_PORT[i])
                except:
                    logger.info('Could not connect to shard %d at IP address: %s port:%s', i + 1, TCP_IP[i], TCP_PORT[i])
                    continue
        except:
            logger.info('Connection error')
        self.NUM_BACKUP_SHARDS = count
        return backupServers

    def getBackupShardConfigInfo(self):
        logger.debug('Reading configuration of backup servers information from %s', self.configFile)
        jsonData = []
        with open(self.configFile) as jsonFile:
            jsonData = json.load(jsonFile)
        TCP_IP = []
        TCP_PORT = []
        TCP_IP.append(jsonData["shard1ip"])
        TCP_PORT.append(int(jsonData["shard1port"]))
        TCP_IP.append(jsonData["shard2ip"])
        TCP_PORT.append(int(jsonData["shard2port"]))
        return TCP_IP, TCP_PORT