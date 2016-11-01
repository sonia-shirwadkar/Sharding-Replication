import json
import os.path
from common import *

def deleteFileMetadata(metadatafile, filename):
	try:
		if (os.path.isfile(metadatafile)):
			lines = open(metadatafile).readlines()
		else:
			lines = ''
		with open(metadatafile, 'wb') as fp:
			for line in lines:
				data = json.loads(line)
				if filename in data.values():
					continue
				else:
					fp.write(line)
	except:
		raise

def addFileMetadata(metadatafile, metadata):
	try:
		deleteFileMetadata(metadatafile, metadata[Keys.FILENAME])
		message = metadata
		fp = open(metadatafile, 'ab')
		fp.write(json.dumps(message) + '\n')
	except:
		raise

def readFileMetadata(metadatafile, filename):
	try:
		val = {}
		message = ''
		if(os.path.isfile(metadatafile)):
			with open(metadatafile) as fp:
				for line in fp:
					data = json.loads(line)
					if filename in data.values():
						val = data
			fp.close()
	except:
		raise
	return val

def deleteCapacityField(metadatafile):
	try:
		if (os.path.isfile(metadatafile)):
			lines = open(metadatafile).readlines()
		else:
			lines = ''
		with open(metadatafile, 'wb') as fp:
			for line in lines:
				data = json.loads(line)
				if Keys.SHARDCAPACITY in data:
					continue
				else:
					fp.write(line)
	except:
		raise

def getCapacityField(metadatafile):
	try:
		capacity = 0
		if (os.path.isfile(metadatafile)):
			with open(metadatafile) as fp:
				for line in fp:
					data = json.loads(line)
					if Keys.SHARDCAPACITY in data:
						capacity = long(data[Keys.SHARDCAPACITY])
			fp.close()
		else:
			capacity = 0
	except:
		raise
	return capacity

def addCapacityField(metadatafile, newCapacity):
	try:
		deleteCapacityField(metadatafile)
		fp = open(metadatafile, 'ab')
		data = Messages.shardcapacity
		data[Keys.SHARDCAPACITY] = newCapacity
		fp.write(json.dumps(data) + '\n')
	except:
		raise

def addToShardCapacity(metadatafile, newCapacity):
	try:
		newCapacity += getCapacityField(metadatafile)
		addCapacityField(metadatafile, newCapacity)
	except:
		raise


