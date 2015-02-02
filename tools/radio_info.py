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

print '''
Radio Address: %s
Radio Version Info: %s
Radio Power Level: %s''' % (radio.address, radio.version_info, radio.power_level)

diag = radio.read_diagnostics()

print 'Diagnostics:'
print json.dumps(diag, sort_keys=True, indent=4, separators=(',', ': '))
