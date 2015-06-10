from ..protocol.vanguard import ProgramUploadMsg, ProgramResultMsg
from ..radio import Radio

import struct
import subprocess
import vanguard.protocol.vanguard

class UploadHandler(object):
    msg_type = ProgramUploadMsg.TYPE
    
    def handle(self, radio, msg):
        self.radio = radio
        self.parse_message(msg)

    def parse_message(self, msg):
        fmt = '!HHHHH' 
        unpacked_data = struct.unpack_from(fmt, msg.message_data)
        self.index = unpacked_data[0]
        self.chunk = unpacked_data[1]
        self.chunk_count = unpacked_data[2]
        prog_name_length = unpacked_data[3]
        prog_data_length = unpacked_data[4]

        fmt = fmt + str(prog_name_length) + 's' + str(prog_data_length-1) + 's'
        second_unpacked_data  = struct.unpack_from(fmt, msg.message_data)

        self.program_name = second_unpacked_data[5]
        self.filename = self.program_name + '.js'
        self.program_data = second_unpacked_data[6]

        with open(self.filename,'a') as output_file:
            output_file.write(self.program_data)  

        self.run_program()

    def run_program(self):
        self.output_file_name = self.program_name + '.log'
        outputFile = open(self.output_file_name,'w')
        process = subprocess.Popen(['nodejs', self.filename],stdout=outputFile)
        process.wait()
        self.exit_code = process.returncode

        with open (self.output_file_name, "r") as output:
            data = output.read().replace('\n', '')
        
        self.radio.send(type='ProgramResultMsg',
                        index=0,
                        chunk=0,
                        chunk_count=1,
                        program_name_length=len(self.program_name),
                        program_data_length=len(data),
                        exit_code=self.exit_code,
                        program_name=self.program_name,
                        program_output_data=data)