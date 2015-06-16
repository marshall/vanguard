from ..protocol.vanguard import PingMsg

class PingHandler(object):
    msg_type = PingMsg.TYPE

    def __init__(self, config):
        pass

    def handle(self, radio, msg):
        radio.send('pong', magic=msg.magic)
