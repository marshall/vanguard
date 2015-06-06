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
logger = logging.getLogger('telemetry-test')

class TelemetryTest(unittest.TestCase):
    cfg = dict(telemetry=dict(interval=5, int_temp_pin=1, ext_temp_pin=2))

    def setUp(self):
        self.patcher = mock.patch.dict('sys.modules', {
            'Adafruit_BBIO': mock.MagicMock(),
            'Adafruit_BBIO.ADC': mock.MagicMock()
        })
        self.patcher.start()
        import Adafruit_BBIO.ADC as ADC
        from vanguard import config, telemetry

        telemetry.ADC = self.ADC = ADC
        self.telemetry = telemetry
        self.config = config.Config(data=self.cfg)
        self.addCleanup(self.patcher.stop)

    def test_calc_temp(self):
        self.ADC.read = lambda pin: 0.858333 if pin == 1 else 0.745

        t = self.telemetry.Telemetry(self.config)
        int_temp = t.calc_temp(1)
        ext_temp = t.calc_temp(2)
        self.assertAlmostEqual(int_temp, 21.6, places=1)
        self.assertAlmostEqual(ext_temp, 18.5, places=1)

        #self.assertEqual(t.redis.llen('telemetry'), 1)
        #data = json.loads(t.redis.lindex('telemetry', -1))

    def test_stats(self):
        opens = {
            '/proc/uptime': mock.mock_open(read_data='1147 0\n'),
            '/proc/stat': mock.mock_open(read_data='cpu  26721690 114128 1984006 795144196 395867 159583 0 0 0 0\n'),
            '/proc/meminfo': mock.mock_open(read_data='MemFree:        236748 kB\n')
        }

        def mock_open(*args):
            return opens[args[0]](*args)

        import __builtin__
        with mock.patch.object(__builtin__, 'open', mock_open):
            t = self.telemetry.Telemetry(self.config)
            stats = t.update_stats()

        self.assertEqual(stats['cpu_usage'], 3)
        self.assertEqual(stats['free_mem'], 236748)
        self.assertEqual(stats['uptime'], 1147)
