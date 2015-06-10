import logging
import os
import sys
import unittest

import mock

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(top_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main-test')

class MainTest(unittest.TestCase):
    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.ADC': mock.MagicMock()})
    def test_main(self):
        from vanguard import main, telemetry
        telemetry.Telemetry.main = mock.MagicMock()
        sys.argv[1:] = ['--logfile', '/tmp/test_main.log', 'telemetry']
        main.main()

        self.assertTrue(telemetry.Telemetry.main.called)
