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
import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('temp-test')

class TempTest(unittest.TestCase):

    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.ADC': mock.MagicMock()})
    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def test_temp(self):
        import Adafruit_BBIO.ADC as ADC
        import temp
        ADC.read = lambda(pin): 0.858333

        t = temp.Temp(config.Config())
        t.on_interval()

        self.assertEqual(t.redis.llen('temps'), 1)
        data = json.loads(t.redis.lindex('temps', -1))
        self.assertAlmostEqual(data['int'], 21.6, places=1)

