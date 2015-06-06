import json
import logging
import os
from StringIO import StringIO
import sys
import time
import unittest

import mock
import mockredis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('beacon-test')

class BeaconTest(unittest.TestCase):
    cfg = dict(radios=dict(primary=dict(type='xtend900',
                                        protocol='vanguard',
                                        uart='UART5',
                                        device='/dev/ttyO5',
                                        baudrate=9600),
                           secondary=dict(type='tx2h',
                                          protocol='aprs',
                                          device='/tmp/kisstnc',
                                          baudrate=1200,
                                          callsign='ABCD-1',
                                          aprs_path='PATH',
                                          ptt_pin='P8_26',
                                          ptt_high=3.0)),
               beacon=dict(interval=5))

    def setUp(self):
        self.KISS = mock.MagicMock()
        self.module_patcher = mock.patch.dict('sys.modules', {
            'Adafruit_BBIO': mock.MagicMock(),
            'Adafruit_BBIO.UART': mock.MagicMock(),
            'Adafruit_BBIO.GPIO': mock.MagicMock(),
            'kiss': mock.MagicMock(KISS=mock.MagicMock(return_value=self.KISS)),
            'redis': mock.MagicMock(),
            'serial': mock.MagicMock(),
            'subprocess': mock.MagicMock()
        })

        self.module_patcher.start()
        self.mock_modules = self.module_patcher.values
        self.mock_modules['redis'].StrictRedis = mockredis.mock_strict_redis_client

        top_dir = os.path.abspath(os.path.dirname(__file__) + '/..')
        sys.path.append(top_dir)
        import vanguard, vanguard.beacon, vanguard.config, \
               vanguard.hab_utils, vanguard.protocol.vanguard, \
               vanguard.protocol.aprs, vanguard.radio, \
               vanguard.xtend900

        self.config = vanguard.config.Config(data=self.cfg)

        self.vanguard = vanguard
        self.vanguard_proto = self.vanguard.protocol.vanguard
        self.aprs_proto = self.vanguard.protocol.aprs
        self.TX2H = vanguard.radio.TX2H
        self.Xtend900 = vanguard.xtend900.Xtend900

        self.beacon = vanguard.beacon.Beacon(self.config)
        self.redis = self.beacon.redis

        self.addCleanup(self.module_patcher.stop)

    def test_radios(self):
        self.assertEqual(len(self.beacon.radios), 2)
        self.assertTrue('primary' in self.beacon.radios)
        self.assertTrue('secondary' in self.beacon.radios)

        p = self.beacon.radios['primary']
        self.assertTrue(isinstance(p.protocol, self.vanguard_proto.VanguardProtocol))
        self.assertEqual(p.uart, 'UART5')
        self.assertTrue(isinstance(p.device, self.Xtend900))
        self.assertEqual(p.baudrate, 9600)

        s = self.beacon.radios['secondary']
        self.assertTrue(isinstance(s.protocol, self.aprs_proto.APRSProtocol))
        print s.device
        self.assertTrue(isinstance(s.device, self.TX2H))
        self.assertEqual(s.baudrate, 1200)
        self.assertEqual(s.callsign, 'ABCD-1')
        self.assertEqual(s.aprs_path, 'PATH')

    def test_location(self):
        self.redis.rpush('location', '{"time": "2015-01-05T22:27:35.412Z", "lat": 12, "lon": 34, "alt": 56, "track": 1.23, "speed": 12.34}')
        primary_write = self.beacon.radios['primary'].device.write = mock.MagicMock()
        secondary_write = self.beacon.radios['secondary'].device.write = mock.MagicMock()

        self.beacon.send_last_entry('location')

        primary_tx_buffer = self.beacon.radios['primary'].tx_buffer
        secondary_tx_buffer = self.beacon.radios['secondary'].tx_buffer

        self.assertEqual(primary_tx_buffer[-1],
                         self.vanguard_proto.LocationMsg.from_data(
                             latitude=12,
                             longitude=34,
                             altitude=56,
                             speed=12.34).as_buffer())

        aprs_formatter = self.aprs_proto.APRSProtocol(callsign='ABCD-1', aprs_path='PATH')
        self.assertEqual(secondary_tx_buffer[-1], aprs_formatter.format_packet(
            '/222735h1200.00N/03400.00EO001/044/A=000184'))

    def test_telemetry(self):
        self.redis.rpush('telemetry', '{}')
        self.redis.rpush('telemetry', '{"int_temp": 23, "ext_temp": 45, "uptime": 1147, "free_mem": 236748, "cpu_usage": 3}')
        primary_write = self.beacon.radios['primary'].device.write = mock.MagicMock()
        secondary_write = self.beacon.radios['secondary'].device.write = mock.MagicMock()

        self.beacon.send_last_entry('telemetry')
        primary_tx_buffer = self.beacon.radios['primary'].tx_buffer
        secondary_tx_buffer = self.beacon.radios['secondary'].tx_buffer

        self.assertEqual(primary_tx_buffer[-1],
                         self.vanguard_proto.TelemetryMsg.from_data(
                            uptime=1147,
                            mode=0,
                            cpu_usage=3,
                            free_mem=231,
                            int_temperature=23,
                            int_humidity=0,
                            ext_temperature=45).as_buffer())

        aprs_formatter = self.aprs_proto.APRSProtocol(callsign='ABCD-1', aprs_path='PATH')
        self.assertEqual(secondary_tx_buffer[-1], aprs_formatter.format_packet(
            'T#001,023,045,003,231,019,00000000'))

    def test_ping(self):
        msg = self.vanguard_proto.PingMsg.from_data(magic=0x1234)
        buf = msg.as_buffer()
        f = StringIO(buf)

        def custom_read(n):
            return f.read(n)

        primary_radio = self.beacon.radios['primary']
        primary_radio.device.read = custom_read
        primary_radio.device.write = mock.MagicMock()
        primary_radio.start()

        self.beacon.handle_packet = mock.MagicMock()
        self.beacon.send_telemetry = mock.MagicMock()
        self.beacon.send_location = mock.MagicMock()
        self.beacon.on_iteration()

        calls = self.beacon.handle_packet.mock_calls
        radio, rcvd_msg = calls[0][1]

        self.assertTrue(self.beacon.handle_packet.called)
        self.assertEqual(radio, primary_radio)
        self.assertEqual(rcvd_msg.as_buffer(), buf)

if __name__ == '__main__':
    unittest.main()
