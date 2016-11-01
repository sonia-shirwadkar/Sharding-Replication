import base64

class EncoderDecoder():
    @classmethod
    def encodeData(self, data):
        return base64.b64encode(data)

    @classmethod
    def decodeData(self, data):
        return base64.b64decode(data)
