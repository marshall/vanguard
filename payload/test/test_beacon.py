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

import beacon
import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('beacon-test')

class BeaconTest(unittest.TestCase):
    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.UART': mock.MagicMock()})
    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def setUp(self):
        self.config = config.Config(data=dict(beacon=dict(
            callsign='ABCD1',
            path='PATH',
            interval=5
        )))
        self.beacon = beacon.Beacon(self.config)
        self.redis = self.beacon.redis

    def test_no_locations(self):
        self.beacon.on_interval()

    def test_beacon(self):
        self.redis.rpush('locations', '{"time": "2015-01-05T22:27:35.412Z", "lat": 12, "lon": 34, "alt": 56, "track": 1.23, "speed": 12.34}')
        self.beacon.send_packet = mock.MagicMock()
        self.beacon.on_interval()

        self.assertTrue(self.beacon.send_packet.called)
        logger.info(self.beacon.send_packet.mock_calls)

        self.beacon.send_packet.assert_called_with(
            'ABCD1>APRS,PATH:/222735h1200.00N/03400.00EO001/044/A=000184')


