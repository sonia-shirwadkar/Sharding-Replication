import platform


BUFFER_SIZE = 1024
if (platform.system() == 'Linux'):
    PATH_SEP = '/'
elif (platform.system() == 'Windows'):
    PATH_SEP = '\\'

##################################################################
# Class:
#     Request
# Description:
#     This class is an enum for all request strings
##################################################################
class Config:
    CONF_HOMEDIR = 'homedir'
    CONF_LISTENPORT = 'listenport'
    CONF_METADATAFILE = 'metadatafile'
    CONF_SHARD1IP = 'shard1ip'
    CONF_SHARD1PORT = 'shard1port'
    CONF_SHARD2IP = 'shard2ip'
    CONF_SHARD2PORT = 'shard2port'
    CONF_SHARD3IP = 'shard3ip'
    CONF_SHARD3PORT = 'shard3port'


class MessageType:
    MSG_BYTESTORED = 'BYTESTORED'
    MSG_DISCONNECT = 'DISCONNECT'
    MSG_DATA = 'DATA'
    MSG_FILEINFO = 'FILEINFO'
    MSG_REQUESTDATA = 'REQUESTDATA'
    MSG_BACKUPDATA = 'BACKUPDATA'
    MSG_METADATA = 'METADATA'
    MSG_TIMESTAMP = 'TIMESTAMP'

	
class Keys:
    MESSAGETYPE = 'MessageType'
    BYTESTORED = 'BytesStored'
    FILENAME = 'Filename'
    FILENAME2 = 'Filename2'
    FILENAME3 = 'Filename3'
    BYTESFROM = 'BytesFrom'
    BYTESTO = 'BytesTo'
    BYTESFROM2 = 'BytesFrom2'
    BYTESTO2 = 'BytesTo2'
    BYTESFROM3 = 'BytesFrom3'
    BYTESTO3 = 'BytesTo3'
    DATA = 'Data'
    SHARDCAPACITY = 'ShardCapacity'
    FILESIZE = 'FileSize'
    TIMESTAMP = ''

class Messages:
    shardcapacity = {Keys.SHARDCAPACITY : 0}
    disconnect = {Keys.MESSAGETYPE : MessageType.MSG_DISCONNECT}
    bytestored = {Keys.MESSAGETYPE : MessageType.MSG_BYTESTORED, Keys.BYTESTORED : 0}
    data = {Keys.MESSAGETYPE : MessageType.MSG_DATA, Keys.FILENAME : '', Keys.BYTESFROM : 0, Keys.BYTESTO : 0, Keys.DATA : 0}
    fileinfo = {
        Keys.MESSAGETYPE : MessageType.MSG_FILEINFO,
        Keys.FILENAME : '',
        Keys.BYTESFROM : 0,
        Keys.BYTESTO : 0,
        Keys.BYTESFROM2 : 0,
        Keys.BYTESTO2 : 0,
        Keys.BYTESFROM3 : 0,
        Keys.BYTESTO3 : 0
        }
    requestdata = {Keys.MESSAGETYPE : MessageType.MSG_REQUESTDATA, Keys.FILENAME : '', Keys.BYTESFROM : 0, Keys.BYTESTO : 0}
    backupdata = {Keys.MESSAGETYPE : MessageType.MSG_BACKUPDATA, Keys.FILENAME : '', Keys.BYTESFROM: 0, Keys.BYTESTO: 0, Keys.DATA : 0}
    metadata = {
        Keys.MESSAGETYPE: MessageType.MSG_METADATA,
        Keys.FILENAME: '',
        Keys.FILESIZE: 0,
        Keys.BYTESFROM: 0,
        Keys.BYTESTO: 0,
        Keys.FILENAME2: '',
        Keys.BYTESFROM2: 0,
        Keys.BYTESTO2: 0,
        Keys.FILENAME3: '',
        Keys.BYTESFROM3: 0,
        Keys.BYTESTO3: 0
    }
    timestamp = {
        Keys.MESSAGETYPE: MessageType.MSG_TIMESTAMP,
        Keys.TIMESTAMP: ''
    }
	
##################################################################