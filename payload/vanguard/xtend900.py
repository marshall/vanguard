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

        self.connected = False
        self.address = '?'
        self.version_info = '?'
        self.power_level = 0

    def connect(self):
        UART.setup(self.uart)
        self.serial = serial.Serial(port=self.device,
                                    baudrate=self.baudrate,
                                    timeout=2)
        self.connected = True
        self.read_config()

    @contextmanager
    def command_mode(self):
        cmd_mode = True
        try:
            cmd_mode = self.enter_command_mode()
            if not cmd_mode:
                raise RuntimeError('Couldn\'t enter command mode')

            yield
        finally:
            if cmd_mode:
                self.leave_command_mode()

    def enter_command_mode(self):
        self.write('+++')
        success = self.read_OK()
        if not success:
            self.log.warn('Couldn\'t enter command mode')

        return success

    def leave_command_mode(self):
        self.write('ATCN\r')
        self.read_AT_lines()

    def read_config(self):
        self.log.info('Reading radio config')
        with self.command_mode():
            self.log.debug('getting address')
            self.write('ATMY\r')
            self.address = self.read_AT_line()

            self.log.debug('address:%s. getting version info', self.address)
            self.write('ATVL\r')
            result = self.read_AT_lines(3)
            if len(result) > 0:
                if 'OK' in result:
                    result.remove('OK')
                self.version_info = '/ '.join(result)

            self.log.debug('version_info:%s. getting power level',
                           self.version_info)
            self.write('ATPL\r')
            result = self.read_AT_lines(1)
            if len(result) > 0:
                self.power_level = int(result[0])

            self.log.debug('power_level=%d', self.power_level)

    def set_power_level(self, power_level):
        with self.command_mode():
            self.write('ATPL %d\r' % self.power_level)
            result = self.read_AT_lines()
            self.log.info('ATPL set lines = %d, (%s)', len(result), ','.join(result))

            self.write('ATPL\r')
            result = self.read_AT_lines(1)
            if len(result) > 0:
                self.power_level = int(result[0])

        return self.power_level == power_level

    def read_diagnostics(self):
        self.diag = dict()

        def hex_cmd(suffix):
            self.write('AT%s\r' % suffix)
            return int(self.read_AT_line(), 16)

        hex_val = lambda: int(self.read_AT_line(), 16)
        with self.command_mode():
            commands = 'AT%s\r' % (','.join(('%V', 'DB', 'ER', 'GD', 'TP', 'TR')))
            self.write(commands)

            self.diag['voltage'] = round(hex_val() / 65536.0, 2)
            self.diag['rx_db'] = hex_val()
            self.diag['rx_err_count'] = hex_val()
            self.diag['rx_good_count'] = hex_val()
            self.diag['board_temp'] = hex_val()
            self.diag['tx_err_count'] = hex_val()

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
            return ''.join(response)

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

    def write_line(self, str):
        self.log.info(str)
        self.write(str + '\r\n')

    def write(self, str):
        self.serial.write(str)
        self.serial.flush()
