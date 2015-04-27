import json
import logging
import os
import sys
import unittest

import mock
import mockredis

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(top_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('temp-test')

class TempTest(unittest.TestCase):

    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.ADC': mock.MagicMock()})
    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def test_temp(self):
        import Adafruit_BBIO.ADC as ADC
        from vanguard import config, main, temp

        temp.ADC = ADC
        ADC.read = lambda pin: 0.858333 if pin == 1 else 0.745

        t = temp.Temp(config.Config(data=dict(
            temp=dict(interval=5, int_temp_pin=1, ext_temp_pin=2)
        )))
        t.on_interval()

        self.assertEqual(t.redis.llen('temps'), 1)
        data = json.loads(t.redis.lindex('temps', -1))
        self.assertAlmostEqual(data['int'], 21.6, places=1)
        self.assertAlmostEqual(data['ext'], 18.5, places=1)


