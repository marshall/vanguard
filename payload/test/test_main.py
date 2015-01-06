import logging
import os
import sys
import unittest

import mock

this_dir = os.path.abspath(os.path.dirname(__file__))
vanguard_dir = os.path.abspath(os.path.join(this_dir, '..', 'vanguard'))
sys.path.append(vanguard_dir)

import main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('main-test')

class MainTest(unittest.TestCase):
    @mock.patch.dict('sys.modules', Adafruit_BBIO=mock.MagicMock())
    @mock.patch.dict('sys.modules', {'Adafruit_BBIO.ADC': mock.MagicMock()})
    def test_main(self):
        import temp
        temp.Temp.main = mock.MagicMock()
        sys.argv[1:] = ['--logfile', '/tmp/test_main.log', 'temp']
        main.main()

        self.assertTrue(temp.Temp.main.called)
