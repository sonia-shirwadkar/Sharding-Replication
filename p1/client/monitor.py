import os
import sys
import csv
import time
import socket
import logging
import platform
from common import *
from threading import Timer
from optparse import OptionParser

FORMAT = "[%(asctime)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(format=FORMAT, level=logging.NOTSET)
logger = logging.getLogger(__name__)
logger.propagate = False

#Global data
BUFFER_SIZE = 1024
MEASUREMENT_TIMER = 10.0
CSV_FILE = 'measurements.csv'
FILESTORE = 'clientfilestore'
if (platform.system() == 'Linux'):
    PATH_SEP = '/'
elif (platform.system() == 'Windows'):
    PATH_SEP = '\\'
NUM_SHARDS = 3

class Monitor(object):
    def __init__(self, configFile):
        self.configFile = configFile
        self.numShards = NUM_SHARDS
        self.timeCol = 0

    def connectToShards(self):
        count = 0
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
                    print 'Connected to shard', i + 1, 'at IP address:', TCP_IP[i], 'port', TCP_PORT[i]
                    logger.info('Connected to shard %d at IP address: %s port:%s', i + 1, TCP_IP[i], TCP_PORT[i])
                except:
                    logger.info('Could not connect to shard %d at IP address: %s port:%s', i + 1, TCP_IP[i], TCP_PORT[i])
                    continue
        except:
            logger.error('Failed to open socket')
            raise
        self.numShards = count

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

    def writeToCSV(self, shardCapacity):
        # print 'Hey'
        try:
            self.timeCol += MEASUREMENT_TIMER
            csvfile = open('measurements.csv', 'ab')
            csvWriter = csv.writer(csvfile)
            data = ((self.timeCol, shardCapacity[0], shardCapacity[1], shardCapacity[2]))
            csvWriter.writerow(data)
            csvfile.close()
        except Exception as e:
            logger.error(str(e))
            raise

    def getMeasurements(self):
        try:
            monitor.connectToShards()
            shardCapacity = self.queryShardCapacities()
            self.writeToCSV(shardCapacity)
            t = Timer(10, self.getMeasurements)
            t.start()
        except Exception as e:
            logger.error(str(e))
            raise

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
        (options, args) = parser.parse_args()
        configFile = options.config
        logger.debug('Config:%s Upload:%s Download:%s', configFile)
    except:
        configFile = ''
        logger.debug('Error in parsing command line args')
    return configFile

if __name__ == '__main__':
    configFile = parseCommandLineArgs()
    monitor = Monitor(configFile)
    csvfile = open(CSV_FILE, 'wb')
    colNames = (('Time', 'Shard1', 'Shard2', 'Shard3'))
    writer = csv.writer(csvfile)
    writer.writerow(colNames)
    csvfile.close()
    monitor.getMeasurements()


