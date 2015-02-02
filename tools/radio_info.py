import os
import socket
import sys

import serial

import Adafruit_BBIO.UART as UART

this_dir = os.path.dirname(os.path.abspath(__file__))
payload_dir = os.path.join(this_dir, '../payload')
sys.path.append(payload_dir)

from vanguard import config

def error(msg):
    print >>sys.stderr, msg
    sys.exit(1)

def read_AT_line():
    response = []
    while True:
        c = ser.read(1)
        if c is None or len(c) == 0 or c[0] == '\r':
            break
        response.append(c[0])

    if len(response) > 0:
        return ''.join(response)

    return None

def read_AT_lines():
    responses = []
    try:
        while True:
            response = read_AT_line()
            if not response:
                break
            responses.append(response)
    except socket.timeout, e:
        pass

    return responses

def write(str):
    try:
        ser.write(str)
        ser.flush()
    except:
        pass

cfg = config.Config()
UART.setup(cfg.beacon.radio_uart)
ser = serial.Serial(port=cfg.beacon.radio_device,
                    baudrate=cfg.beacon.radio_baudrate,
                    timeout=2)


ser.write('+++')
ser.flush()

print 'Entering command mode'
msg = ser.read(3)
if msg != 'OK\r':
    error('command mode not acknowledged')


print 'Getting address'
write('ATMY\r')
address = read_AT_line()

print 'Getting version'
write('ATVL\r')
result = read_AT_lines()
version_info = ''
if len(result) > 0:
    if 'OK' in result:
        result.remove('OK')
    version_info = '/'.join(result)

print 'Getting power level'
write('ATPL\r')
result = read_AT_lines()
power_level = None
if len(result) > 0:
    power_level = result[0]

write('ATCN\r')
read_AT_lines()

print '''
Radio Address: %s
Radio Version Info: %s
Radio Power Level: %s''' % (address, version_info, power_level)
