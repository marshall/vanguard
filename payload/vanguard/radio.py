import logging
import kiss
import threading

from protocol.aprs import APRSFormatter
from protocol.vanguard import VanguardFormatter, MsgReader

from xtend900 import Xtend900

class Radio(threading.Thread):
    daemon = True
    def __init__(self, type='xtend900', protocol='vanguard',
                       device='/dev/ttyO5', baudrate=9600, uart='UART5',
                       **kwargs):
        super(Radio, self).__init__()
        self.rx_lock = threading.Lock()
        self.rx_event = threading.Event()
        self.rx_buffer = []
        self.tx_lock = threading.Lock()
        self.tx_event = threading.Event()
        self.tx_buffer = []
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

    def handle_msg(self, msg):
        self.rx_lock.acquire()
        self.rx_buffer.append(msg)
        self.rx_lock.release()
        self.rx_event.set()

    def run(self):
        while True:
            if self.protocol == 'vanguard':
                msg = MsgReader().read(self.device)
                if msg:
                    self.handle_msg(msg)

            if not self.tx_event.wait(1):
                continue

            self.tx_event.clear()
            self.tx_lock.acquire()
            for packet in self.tx_buffer:
                self.device.write(packet)
            self.tx_buffer = []
            self.tx_lock.release()

    def recv(self, timeout=None):
        if not self.rx_event.wait(timeout):
            return None

        self.rx_event.clear()
        self.rx_lock.acquire()
        result = self.rx_buffer.pop(0)
        self.rx_lock.release()
        return result

    def send(self, type, *args, **kwargs):
        formatter = getattr(self.formatter, 'format_' + type)
        data = formatter(*args, **kwargs)
        packet = self.formatter.format_packet(data)

        self.tx_lock.acquire()
        self.tx_buffer.append(packet)
        self.tx_lock.release()
        self.tx_event.set()

    def send_location(self, *args, **kwargs):
        self.send('location', *args, **kwargs)

    def send_telemetry(self, *args, **kwargs):
        self.send('telemetry', *args, **kwargs)
