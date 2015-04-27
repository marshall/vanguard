import json
import logging
import os
import sys
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
                           secondary=dict(type='kisstnc',
                                          protocol='aprs',
                                          device='/tmp/kisstnc',
                                          baudrate=1200,
                                          callsign='ABCD-1',
                                          path='PATH')),
               beacon=dict(position_interval=5,
                           telemetry_interval=5))

    def setUp(self):
        self.KISS = mock.MagicMock()
        self.module_patcher = mock.patch.dict('sys.modules', {
            'Adafruit_BBIO': mock.MagicMock(),
            'Adafruit_BBIO.UART': mock.MagicMock(),
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
               vanguard.protocol.aprs, vanguard.xtend900

        self.config = vanguard.config.Config(data=self.cfg)

        self.vanguard = vanguard
        self.vanguard_proto = self.vanguard.protocol.vanguard
        self.aprs_proto = self.vanguard.protocol.aprs
        self.beacon = vanguard.beacon.Beacon(self.config)
        self.redis = self.beacon.redis
        self.addCleanup(self.module_patcher.stop)

    def test_radios(self):
        self.assertEqual(len(self.beacon.radios), 2)
        self.assertTrue('primary' in self.beacon.radios)
        self.assertTrue('secondary' in self.beacon.radios)

        p = self.beacon.radios['primary']
        self.assertEqual(p.protocol, 'vanguard')
        self.assertEqual(p.uart, 'UART5')
        self.assertTrue(isinstance(p.device, self.vanguard.xtend900.Xtend900))
        self.assertEqual(p.baudrate, 9600)

        s = self.beacon.radios['secondary']
        self.assertEqual(s.protocol, 'aprs')
        self.assertEqual(s.device, self.KISS)
        self.assertEqual(s.baudrate, 1200)
        self.assertEqual(s.callsign, 'ABCD-1')
        self.assertEqual(s.path, 'PATH')

    def test_location(self):
        self.redis.rpush('locations', '{"time": "2015-01-05T22:27:35.412Z", "lat": 12, "lon": 34, "alt": 56, "track": 1.23, "speed": 12.34}')
        primary_write = self.beacon.radios['primary'].device.write = mock.MagicMock()
        secondary_write = self.beacon.radios['secondary'].device.write = mock.MagicMock()
        self.beacon.send_location()

        self.assertTrue(primary_write.called)
        self.assertTrue(secondary_write.called)
        primary_write.assert_called_with(self.vanguard_proto.LocationMsg.from_data(
                                           latitude=12,
                                           longitude=34,
                                           altitude=56,
                                           speed=12.34).as_buffer())

        aprs_formatter = self.aprs_proto.APRSFormatter(callsign='ABCD-1', path='PATH')
        secondary_write.assert_called_with(aprs_formatter.format_packet(
            '/222735h1200.00N/03400.00EO001/044/A=000184'))

    def test_telemetry(self):
        self.redis.rpush('temps', '{"int": 23, "ext": 45}')
        primary_write = self.beacon.radios['primary'].device.write = mock.MagicMock()
        secondary_write = self.beacon.radios['secondary'].device.write = mock.MagicMock()

        opens = {
            '/proc/uptime': mock.mock_open(read_data='1147 0\n'),
            '/proc/stat': mock.mock_open(read_data='cpu  26721690 114128 1984006 795144196 395867 159583 0 0 0 0\n'),
            '/proc/meminfo': mock.mock_open(read_data='MemFree:        236748 kB\n')
        }

        def mock_open(*args):
            return opens[args[0]](*args)

        import __builtin__
        with mock.patch.object(__builtin__, 'open', mock_open):
            self.beacon.send_telemetry()

        self.assertTrue(primary_write.called)
        self.assertTrue(secondary_write.called)

        primary_write.assert_called_with(self.vanguard_proto.TelemetryMsg.from_data(
                uptime=1147,
                mode=0,
                cpu_usage=3,
                free_mem=231,
                int_temperature=23,
                int_humidity=0,
                ext_temperature=45).as_buffer())

        aprs_formatter = self.aprs_proto.APRSFormatter(callsign='ABCD-1', path='PATH')
        secondary_write.assert_called_with(aprs_formatter.format_packet(
            'T#000,023,045,003,231,019,00000000'))

if __name__ == '__main__':
    unittest.main()
