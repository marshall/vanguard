from contextlib import contextmanager
import os
import socket
import sys
import threading

import Adafruit_BBIO.UART as UART
import serial

import looper

class Xtend900(looper.Looper):
    PL_1MW    = 0
    PL_10MW   = 1
    PL_100MW  = 2
    PL_500MW  = 3
    PL_1000MW = 4

    def __init__(self, device='/dev/ttyO5', baudrate=9600, uart='UART5'):
        super(Xtend900, self).__init__()
        self.device = device
        self.baudrate = baudrate
        self.uart = uart

        self.cmd_mode = 0
        self.connected = False
        self.diag = dict()
        self.address = '?'
        self.power_level = 0

    def connect(self):
        UART.setup(self.uart)
        self.serial = serial.Serial(port=self.device,
                                    baudrate=self.baudrate,
                                    timeout=5)
        self.connected = True

        #with self.command_mode():
        #    self.read_config()
        #    self.read_diagnostics()

    @contextmanager
    def command_mode(self):
        try:
            self.enter_command_mode()
            if not self.cmd_mode:
                raise RuntimeError('Couldn\'t enter command mode')

            yield
        finally:
            self.leave_command_mode()

    def enter_command_mode(self):
        if self.cmd_mode > 0:
            self.cmd_mode += 1
            return True

        self.write('+++')
        success = self.read_OK()
        if not success:
            self.log.warn('Couldn\'t enter command mode')
        else:
            self.cmd_mode += 1

        return success

    def leave_command_mode(self):
        if self.cmd_mode == 1:
            self.write_AT_command('CN')
            self.read_AT_lines()
        self.cmd_mode -= 1

    def read_config(self):
        self.log.info('Reading radio config')

        with self.command_mode():
            self.write_AT_commands('MY', 'PL')
            self.address = self.read_AT_hex()

            result = self.read_AT_lines(1)
            if len(result) > 0:
                self.power_level = int(result[0])

    def set_power_level(self, power_level):
        with self.command_mode():
            self.write_AT_command('PL', str(self.power_level))
            result = self.read_AT_lines()

            self.write_AT_command('PL')
            result = self.read_AT_lines(1)
            if len(result) > 0:
                self.power_level = int(result[0])

        return self.power_level == power_level

    def read_diagnostics(self):
        with self.command_mode():
            self.write_AT_commands('VL', '%V', 'DB', 'ER', 'GD', 'TP', 'TR')

            result = self.read_AT_lines(2)
            if len(result) > 0:
                if 'OK' in result:
                    result.remove('OK')
                self.diag['version_info'] = [r.strip() for r in result]

            self.diag['voltage'] = round(self.read_AT_hex() / 65536.0, 3)

            self.diag['rx_db'] = -self.read_AT_hex()
            if self.diag['rx_db'] == -0x8000:
                self.diag['rx_db'] = 0

            self.diag['rx_err_count'] = self.read_AT_hex()
            self.diag['rx_good_count'] = self.read_AT_hex()
            self.diag['board_temp'] = self.read_AT_hex()
            self.diag['tx_err_count'] = self.read_AT_hex()

        return self.diag

    def read_OK(self):
        try:
            msg = self.serial.read(3)
            return msg == 'OK\r'
        except socket.timeout, e:
            return False

    def read_AT_line(self):
        response = []
        while True:
            c = self.serial.read(1)
            if c is None or len(c) == 0 or c[0] == '\r':
                break
            response.append(c[0])

        if len(response) > 0:
            line = ''.join(response)
            self.log.debug('<< %s', line)
            return line

        return None

    def read_AT_lines(self, n=0):
        responses = []
        count = 0
        try:
            while True:
                response = self.read_AT_line()
                if not response:
                    break
                responses.append(response)
                count += 1
                if n > 0 and n == count:
                    break
        except socket.timeout, e:
            pass

        return responses

    def read_AT_hex(self):
        return int(self.read_AT_line(), 16)

    def write_AT_command(self, command, *args):
        cmd = 'AT%s' % command
        if len(args) > 0:
            cmd += ' ' + (' '.join(args))

        self.write('%s\r' % cmd)

    def write_AT_commands(self, *commands):
        self.write('AT%s\r' % ','.join(commands))

    def write_line(self, str):
        self.log.info(str)
        self.write(str + '\r\n')

    def write(self, str):
        self.log.debug('>> %s', str.replace('\r\n', ''))
        self.serial.write(str)
        self.serial.flush()
