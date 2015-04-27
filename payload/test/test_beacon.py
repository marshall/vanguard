import json
import logging
import os
import sys
import unittest

import mock
import mockredis


this_dir = os.path.abspath(os.path.dirname(__file__))
vanguard_dir = os.path.abspath(os.path.join(this_dir, '..', 'vanguard'))
sys.path.append(vanguard_dir)


import config
import proto

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('beacon-test')

class BeaconTest(unittest.TestCase):
    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.UART': mock.MagicMock()})
    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    @mock.patch.dict('sys.modules', subprocess = mock.MagicMock())
    def setUp(self):
        import beacon
        self.config = config.Config(data=dict(beacon=dict(
            callsign='ABCD1',
            path='PATH',
            position_interval=5,
            telemetry_interval=5
        )))
        self.beacon_module = beacon
        self.beacon = beacon.Beacon(self.config)
        self.redis = self.beacon.redis

        import subprocess
        self.subprocess = subprocess

    def test_no_locations(self):
        self.beacon.on_interval()

    def test_beacon(self):
        self.redis.rpush('locations', '{"time": "2015-01-05T22:27:35.412Z", "lat": 12, "lon": 34, "alt": 56, "track": 1.23, "speed": 12.34}')
        self.redis.rpush('temps', '{"int": 23}')
        self.subprocess.check_output = lambda *args: '{"uptime": 1147,"total_procs": 100,"cpu_usage": 1.2,"total_mem": 510840,"free_mem": 296748}\n'
        self.beacon.send_message = mock.MagicMock()

        self.beacon.on_interval()

        self.assertTrue(self.beacon.send_message.called)
        calls = [mock.call(proto.LocationMsg,
                           latitude=12,
                           longitude=34,
                           altitude=56,
                           speed=12.34),
                 mock.call(proto.TelemetryMsg,
                           uptime=1147,
                           mode=0,
                           cpu_usage=1,
                           free_mem=289,
                           int_temperature=23,
                           int_humidity=0,
                           ext_temperature=0)]

        self.assertEquals(self.beacon.send_message.call_args_list, calls)

if __name__ == '__main__':
    unittest.main()
