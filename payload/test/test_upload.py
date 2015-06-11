from StringIO import StringIO

import logging
import mock
import mockredis
import os
import shutil
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
        #Set up partially received program where message1 has already been received
        shutil.copytree('uploads/testCase','uploads/programs/helloworld') 
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

        self.beacon.handle_packet(self.primary_radio,message3)
        self.beacon.handle_packet(self.primary_radio,message2)

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
        #send a js file that sends back the contents of ./__init__.py in multiple result messages
        with open('__init__.py', 'r') as input_file:
            test_data = input_file.read()
        with open('test_upload_helper.js','r') as js_file:
            js_data = js_file.read()
        prog_data = 'console.log("' + test_data + '")'
        program_name = 'helloworld'

        result_string1 = test_data[0:235]
        result_string2 = test_data[235:470]
        result_string3 = test_data[470:] + '\n'

        message = self.vanguard_proto.ProgramUploadMsg.from_data(index=0, 
                                                                  chunk=1,
                                                                  chunk_count=1,
                                                                  program_name_len=len(program_name),
                                                                  program_data_len=len(js_data),
                                                                  program_name=program_name,
                                                                  program_upload_data=js_data)

        self.beacon.handle_packet(self.primary_radio,message)

        calls = [mock.call(index=0, type='ProgramResultMsg', chunk=1, exit_code=0, program_name_length=len(program_name), 
                      program_data_length=len(result_string1), program_name=program_name, chunk_count=3, program_output_data=result_string1),
                 mock.call(index=1, type='ProgramResultMsg', chunk=2, exit_code=0, program_name_length=len(program_name), 
                      program_data_length=len(result_string2), program_name=program_name, chunk_count=3, program_output_data=result_string2),
                 mock.call(index=2, type='ProgramResultMsg', chunk=3, exit_code=0, program_name_length=len(program_name),
                      program_data_length=len(result_string3), program_name=program_name, chunk_count=3, program_output_data=result_string3)]
        
        self.primary_radio.send.assert_has_calls(calls)

    def tearDown(self):
        try:
            shutil.rmtree('./uploads/programs/helloworld')
        except OSError:
            pass
