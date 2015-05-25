from ..protocol.vanguard import PingMsg

class PingHandler(object):
    msg_type = PingMsg.TYPE

    def handle(self, radio, msg):
        radio.send('pong', magic=msg.magic)
