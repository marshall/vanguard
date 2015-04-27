import logging
import kiss

from protocol.aprs import APRSFormatter
from protocol.vanguard import VanguardFormatter

from xtend900 import Xtend900

class Radio(object):
    def __init__(self, type='xtend900', protocol='vanguard',
                       device='/dev/ttyO5', baudrate=9600, uart='UART5',
                       **kwargs):

        self.type = type
        self.protocol = protocol
        self.baudrate = baudrate
        self.uart = uart

        if type == 'xtend900':
            self.device = Xtend900(device=device,
                                   baudrate=baudrate,
                                   uart=uart)
        elif type == 'kisstnc':
            self.device = kiss.KISS(device, baudrate)
        else:
            raise Exception('Unknown device type: %s' % type)

        if protocol == 'vanguard':
            self.formatter = VanguardFormatter(**kwargs)
        elif protocol == 'aprs':
            self.formatter = APRSFormatter(**kwargs)
        else:
            raise Exception('Unknown protocol: %s' % protocol)

        for key, val in kwargs.iteritems():
            setattr(self, key, val)

        self.device.start()

    def send(self, type, *args, **kwargs):
        formatter = getattr(self.formatter, 'format_' + type)
        data = formatter(*args, **kwargs)
        self.device.write(self.formatter.format_packet(data))

    def send_location(self, *args, **kwargs):
        self.send('location', *args, **kwargs)

    def send_telemetry(self, *args, **kwargs):
        self.send('telemetry', *args, **kwargs)
