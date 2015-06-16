from ..protocol.vanguard import ProgramUploadMsg, ProgramResultMsg
from ..radio import Radio

import math
import os
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

        fmt = fmt + str(prog_name_length) + 's' + str(prog_data_length) + 's'
        second_unpacked_data  = struct.unpack_from(fmt, msg.message_data)

        self.program_name = second_unpacked_data[5]
        self.filename = self.program_name + '.js'
        self.program_data = second_unpacked_data[6]
        self.directory = os.path.dirname(os.path.dirname(os.path.dirname(__file__))) + '/test/uploads/programs/' + self.program_name + '/'
        self.handle_chunk()

    def handle_chunk(self):
        fmt_str = '!' + str(self.chunk_count) + '?'

        if not os.path.exists(self.directory): # received first chunk of a new program 
            os.makedirs(self.directory)
            bool_arr = [False] * self.chunk_count
            bool_arr[self.chunk - 1] = True
            with open(self.directory + self.program_name + '.kbf', 'w+') as index_file: #.kbf-Kubos Binary Format
                index_file.write(struct.pack(fmt_str, *bool_arr))
            if self.chunk_count == 1:
                self.store_chunk()
                self.assemble_file()
        else:  #This chunk is from a partially received program
            index_struct = struct.Struct(fmt_str)
            contents = []
            with open(self.directory + self.program_name + '.kbf', 'rb') as index_file:
                while True:
                    buf = index_file.read(index_struct.size)
                    if len(buf) != index_struct.size:
                        break
                    contents.extend(index_struct.unpack_from(buf))     

            contents[self.chunk - 1] = True

            with open(self.directory + self.program_name + '.kbf', 'w') as index_file:
                index_file.write(struct.pack(fmt_str, *contents))

            if all(contents):
                self.store_chunk()
                self.assemble_file()
                return
        self.store_chunk()

    def store_chunk(self): 
        with open(self.directory  + '/' + str(self.chunk) + '.dat', 'w+') as chunk_file:
            chunk_file.write(self.program_data)

    def assemble_file(self):
        with open(self.directory + '/' + self.filename, 'w') as program_file:
            for nums in range(self.chunk_count):
                with open(self.directory + str(nums + 1) + '.dat','r') as chunk_file:
                    chunk_data = chunk_file.read()
                    program_file.write(chunk_data)
        self.run_program()

    def run_program(self):
        self.output_file_name = self.directory + self.program_name + '.log'
        output_file = open(self.output_file_name,'w')
        process = subprocess.Popen(['nodejs', self.directory + self.filename], stdout=output_file)
        process.wait()
        self.exit_code = process.returncode
        self.send_result()

    def send_result(self):
        max_data_length = 256 - (vanguard.protocol.vanguard.ProgramResultMsg.data_struct.size + len(self.program_name)) 
        output_length = os.path.getsize(self.output_file_name)
        num_output_chunks = output_length / float(max_data_length)
        num_output_chunks = int(math.ceil(num_output_chunks))

        with open (self.output_file_name, "rb") as output_file:
            for output_chunk in range(num_output_chunks):
                chunk_str = output_file.read(max_data_length)
                self.radio.send(type='ProgramResultMsg',
                                index=output_chunk,
                                chunk=output_chunk + 1,
                                chunk_count=num_output_chunks,
                                program_name_length=len(self.program_name),
                                program_data_length=len(chunk_str),
                                exit_code=self.exit_code,
                                program_name=self.program_name,
                                program_output_data=chunk_str)
