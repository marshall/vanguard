import unittest
import os
import logging

import mock
import mockredis
from StringIO import StringIO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('upload-test')

class UploadTestCase(unittest.TestCase):
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
            'serial': mock.MagicMock()
        })
        self.module_patcher.start()

        import vanguard, vanguard.beacon, vanguard.config, vanguard.protocol.vanguard

        self.mock_modules = self.module_patcher.values
        self.vanguard = vanguard
        self.config = vanguard.config.Config(data=self.cfg)
        self.beacon = vanguard.beacon.Beacon(self.config)
        self.addCleanup(self.module_patcher.stop)
        self.vanguard_proto = self.vanguard.protocol.vanguard

    def test_upload_handler(self):
        buf = self.vanguard_proto.ProgramUploadMsg.from_data(index=0, 
                                                             chunk=0,
                                                             chunk_count=1,
                                                             program_name_len=10,
                                                             program_data_len=26,
                                                             program_name='helloworld',
                                                             program_upload_data='console.log("helloworld")'
                                                             ).as_buffer()
        f = StringIO(buf)

        def custom_read(n):
            return f.read(n)

        primary_radio = self.beacon.radios['primary']
        primary_radio.device.read = custom_read
        primary_radio.device.send = mock.MagicMock()
        primary_radio.send = mock.MagicMock()
        primary_radio.start()

        self.beacon.send_telemetry = mock.MagicMock()
        self.beacon.send_location = mock.MagicMock()
        self.beacon.on_iteration()

        referenceMsg = self.vanguard_proto.ProgramResultMsg.from_data(index=0,
                                                                      chunk=0,
                                                                      chunk_count=1,
                                                                      program_name_length=10,
                                                                      program_data_length=10,
                                                                      exit_code=0,
                                                                      program_name='helloworld',
                                                                      program_output_data='helloworld').as_buffer()

        name, args, kwargs = primary_radio.send.mock_calls[0]
        sentMsg = self.vanguard_proto.ProgramResultMsg.from_data(index=kwargs.get('index'),
                                                                 chunk=kwargs.get('chunk'),
                                                                 chunk_count=kwargs.get('chunk_count'),
                                                                 program_name_length=kwargs.get('program_name_length'),
                                                                 program_data_length=kwargs.get('program_data_length'),
                                                                 exit_code=kwargs.get('exit_code'),
                                                                 program_name=kwargs.get('program_name'),
                                                                 program_output_data=kwargs.get('program_output_data')).as_buffer()

        self.assertEqual(sentMsg, referenceMsg) 

    def tearDown(self):
        try:
            os.remove('helloworld.js')
            os.remove('helloworld.log')        
        except OSError:
            pass
        
