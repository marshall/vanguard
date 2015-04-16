import json
import os
import socket
import sys

this_dir = os.path.dirname(os.path.abspath(__file__))
payload_dir = os.path.join(this_dir, '../payload')
sys.path.append(payload_dir)

from vanguard.config import Config
from vanguard.xtend900 import Xtend900
import vanguard.log

vanguard.log.setup()
cfg = Config()
radio = Xtend900(device=cfg.beacon.radio_device,
                 baudrate=cfg.beacon.radio_baudrate,
                 uart=cfg.beacon.radio_uart)


radio.connect()

levels = ['1mW', '10mW', '100mW', '500mW', '1W']

print '''
Version Info: {version_info}
Radio Address: 0x{addr:04X}
Radio Power Level: {level_str} ({level})
Board Temp: {board_temp} C
Voltage: {voltage} V
Rcv Signal: {rx_db} dB
Rcv Err Count: {rx_err_count}
Rcv Good Count: {rx_good_count}
Xmit Err Count: {tx_err_count}

'''.format(addr=radio.address,
           level=radio.power_level,
           level_str=levels[radio.power_level],
           **radio.diag)

