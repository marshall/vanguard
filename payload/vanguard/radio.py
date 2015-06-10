import base64
from collections import deque
from contextlib import contextmanager
import logging
import threading
import time

import Adafruit_BBIO.GPIO as GPIO
import kiss

from protocol.aprs import APRSProtocol
from protocol.vanguard import VanguardProtocol

from xtend900 import Xtend900

class Radio(threading.Thread):
    daemon = True
    def __init__(self, type='xtend900', protocol='vanguard', **kwargs):
        super(Radio, self).__init__()
        self.log = logging.getLogger('radio.' + type)
        self.rx_lock = threading.Lock()
        self.rx_event = threading.Event()
        self.rx_buffer = deque([], 10)
        self.tx_lock = threading.Lock()
        self.tx_event = threading.Event()
        self.tx_buffer = deque([], 10)
        self.type = type

        if protocol not in protocols:
            raise Exception('Unknown protocol: %s' % protocol)

        if type not in devices:
            raise Exception('Unknown device type: %s' % type)

        kwargs.pop('device')
        for key, val in kwargs.iteritems():
            setattr(self, key, val)

        self.protocol = protocols[protocol](**kwargs)
        self.device_kwargs = kwargs
        self.reconnect = 10
        self.device = None

    def ensure_connected(self):
        if self.device:
            return
        try:
            self.device = devices[self.type](**self.device_kwargs)
            self.device.start()
        except:
            self.log.exception('Failed to connect to %s radio', self.type)
            self.device = None

    def handle_msg(self, msg):
        with self.rx_lock:
            self.rx_buffer.append(msg)
        self.rx_event.set()

    @contextmanager
    def tx(self):
        if hasattr(self.device, 'tx_start'):
            self.device.tx_start()

        with self.tx_lock:
            yield

        if hasattr(self.device, 'tx_stop'):
            self.device.tx_stop()

    def on_iteration(self):
        self.ensure_connected()
        if not self.device:
            self.log.info('Attempting connection again in %d sec', self.reconnect)
            time.sleep(self.reconnect)
            self.reconnect *= 2
            return

        if hasattr(self.protocol, 'read_message'):
            msg = self.protocol.read_message(self.device)
            if msg:
                self.handle_msg(msg)

        if not self.tx_event.wait(0.1):
            return

        self.tx_event.clear()

        with self.tx():
            for packet in self.tx_buffer:
                self._write_sync(packet)
            self.tx_buffer = []

    def run(self):
        while True:
            self.on_iteration()

    def _write_sync(self, packet):
        self.log.debug('>> %s', base64.b64encode(packet))
        self.device.write(packet)

    def recv(self, timeout=None):
        if not self.rx_event.wait(timeout):
            return None

        with self.rx_lock:
            result = self.rx_buffer.pop(0)
            if len(self.rx_buffer) == 0:
                self.rx_event.clear()

        return result

    def send(self, type, *args, **kwargs):
        formatter = getattr(self.protocol, 'format_' + type)
        if not formatter:
            self.log.error('No formatter found for %s' % type)
            return

        data = formatter(*args, **kwargs)
        packet = self.protocol.format_packet(data)

        with self.tx_lock:
            self.tx_buffer.append(packet)
        self.tx_event.set()

    def send_beacon(self, location=None, telemetry=None):
        if location:
            self.send('location', **location)

        if telemetry:
            self.send('telemetry', **telemetry)

# We use a custom audio circuit, PTT over GPIO, and direwolf to modulate
# data to the Radiometrix TX2H
class TX2H(object):
    def __init__(self, device='/tmp/kisstnc', baudrate=1200, ptt_pin=None,
                 ptt_high=None, **kwargs):
        self.kiss = kiss.KISS(device, baudrate)
        self.ptt_pin = ptt_pin
        self.ptt_high = ptt_high
        self.write = self.kiss.write
        self.start = self.kiss.start

    def tx_start(self):
        if not self.ptt_pin:
            return

        GPIO.setup(self.ptt_pin, GPIO.OUT)
        GPIO.output(self.ptt_pin, GPIO.HIGH)
        time.sleep(self.ptt_high)

    def tx_stop(self):
        if not self.ptt_pin:
            return
        time.sleep(self.ptt_high)
        GPIO.output(self.ptt_pin, GPIO.LOW)

protocols = dict(vanguard=VanguardProtocol, aprs=APRSProtocol)
devices = dict(xtend900=Xtend900, tx2h=TX2H)
