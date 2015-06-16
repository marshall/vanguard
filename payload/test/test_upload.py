from StringIO import StringIO

import logging
import math
import mock
import mockredis
import os
import shutil
import tempfile
import unittest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('upload-test')

class UploadTestCase(unittest.TestCase):
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
        self.cfg['work_dir'] = tempfile.mkdtemp()
        self.KISS = mock.MagicMock()
        self.module_patcher = mock.patch.dict('sys.modules', {
            'Adafruit_BBIO': mock.MagicMock(),
            'Adafruit_BBIO.UART': mock.MagicMock(),
            'Adafruit_BBIO.GPIO': mock.MagicMock(),
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

        self.primary_radio = self.beacon.radios['primary']
        self.primary_radio.send = mock.MagicMock()
        self.beacon.send_telemetry = mock.MagicMock()
        self.beacon.send_location = mock.MagicMock()

    def test_single_chunk(self):
        program_name = 'helloworld'
        program_data = 'console.log("helloworld")'
        message = self.vanguard_proto.ProgramUploadMsg.from_data(index=0,
                                                                 chunk=1,
                                                                 chunk_count=1,
                                                                 program_name_len=len(program_name),
                                                                 program_data_len=len(program_data),
                                                                 program_name=program_name,
                                                                 program_upload_data=program_data)
        self.beacon.handle_packet(self.primary_radio,message)

        self.primary_radio.send.assert_called_with(type='ProgramResultMsg',
                                                   index=0,
                                                   chunk=1,
                                                   chunk_count=1,
                                                   program_name_length=10,
                                                   program_data_length=11,
                                                   exit_code=0,
                                                   program_name='helloworld',
                                                   program_output_data='helloworld\n')

    def test_multi_chunk(self):
        message1 = self.vanguard_proto.ProgramUploadMsg.from_data(index=0, 
                                                                  chunk=1,
                                                                  chunk_count=3,
                                                                  program_name_len=10,
                                                                  program_data_len=7,
                                                                  program_name='helloworld',
                                                                  program_upload_data='console')
        message2 = self.vanguard_proto.ProgramUploadMsg.from_data(index=1, 
                                                                  chunk=2,
                                                                  chunk_count=3,
                                                                  program_name_len=10,
                                                                  program_data_len=5,
                                                                  program_name='helloworld',
                                                                  program_upload_data='.log(')
        message3 = self.vanguard_proto.ProgramUploadMsg.from_data(index=2,
                                                                  chunk=3,
                                                                  chunk_count=3,
                                                                  program_name_len=10,
                                                                  program_data_len=13,
                                                                  program_name='helloworld',
                                                                  program_upload_data='"helloworld")')

        self.beacon.handle_packet(self.primary_radio,message2)
        self.beacon.handle_packet(self.primary_radio,message3)
        self.beacon.handle_packet(self.primary_radio,message1)

        self.primary_radio.send.assert_called_with(type='ProgramResultMsg',
                                                   index=0,
                                                   chunk=1,
                                                   chunk_count=1,
                                                   program_name_length=10,
                                                   program_data_length=11,
                                                   exit_code=0,
                                                   program_name='helloworld',
                                                   program_output_data='helloworld\n')

    def test_partially_received(self):
        # Set up partially received program where message1 has already been received
        program_dir = self.cfg['work_dir'] + '/uploads/programs/helloworld'
        testcase_dir = os.path.dirname(os.path.abspath(__file__)) + '/uploads/testCase'
        shutil.copytree(testcase_dir, program_dir)
        message2 = self.vanguard_proto.ProgramUploadMsg.from_data(index=1,
                                                                  chunk=2,
                                                                  chunk_count=3,
                                                                  program_name_len=10,
                                                                  program_data_len=5,
                                                                  program_name='helloworld',
                                                                  program_upload_data='.log(')

        message3 = self.vanguard_proto.ProgramUploadMsg.from_data(index=2,
                                                                  chunk=3,
                                                                  chunk_count=3,
                                                                  program_name_len=10,
                                                                  program_data_len=13,
                                                                  program_name='helloworld',
                                                                  program_upload_data='"helloworld")')

        self.beacon.handle_packet(self.primary_radio, message3)
        self.beacon.handle_packet(self.primary_radio, message2)

        self.primary_radio.send.assert_called_with(type='ProgramResultMsg',
                                                   index=0,
                                                   chunk=1,
                                                   chunk_count=1,
                                                   program_name_length=10,
                                                   program_data_length=11,
                                                   exit_code=0,
                                                   program_name='helloworld',
                                                   program_output_data='helloworld\n')

    def test_multi_chunk_result(self): 
        # send a js file that sends back the contents of ./__init__.py in
        # multiple result messages
        this_dir = os.path.dirname(os.path.abspath(__file__))
        js_file = this_dir + '/test_upload_helper.js'
        program_name = 'multi_chunk_result'

        with open(js_file,'r') as f:
            js_data = f.read()

        # This matches the output of test_uploader_helper.js exactly!
        lorem_ipsum = 'Lorem ipsum\n' * 50
        chunk_len = self.vanguard_proto.ProgramResultMsg.max_data_len(program_name)
        chunk_count = int(math.ceil(len(lorem_ipsum) / float(chunk_len)))
        calls = []
        i = 0
        for index in range(0, chunk_count):
            start = index * chunk_len
            chunk = lorem_ipsum[start:start+chunk_len]
            calls.append(mock.call(index=i,
                                   type='ProgramResultMsg',
                                   chunk=i + 1,
                                   exit_code=0,
                                   program_name_length=len(program_name),
                                   program_data_length=len(chunk),
                                   program_name=program_name,
                                   chunk_count=chunk_count,
                                   program_output_data=chunk))
            i += 1

        message = self.vanguard_proto.ProgramUploadMsg.from_data(index=0,
                                                                 chunk=1,
                                                                 chunk_count=1,
                                                                 program_name_len=len(program_name),
                                                                 program_data_len=len(js_data),
                                                                 program_name=program_name,
                                                                 program_upload_data=js_data)

        self.beacon.handle_packet(self.primary_radio,message)
        self.primary_radio.send.assert_has_calls(calls)

    def tearDown(self):
        try:
            shutil.rmtree(self.cfg['work_dir'])
        except OSError:
            pass
