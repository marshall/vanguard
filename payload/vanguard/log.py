import base64
import json
import logging
import logging.handlers
import sys

from pythonjsonlogger import jsonlogger

DATA = 5 # between 0 and DEBUG
DEFAULT_FILENAME = '/var/log/vanguard.log'

class VanguardLogger(logging.Logger):
    def __init__(self, name):
        super(VanguardLogger, self).__init__(name)

def setup(filename=DEFAULT_FILENAME, debug_stdout=False):
    logging.setLoggerClass(VanguardLogger)
    logging.addLevelName(DATA, 'DATA')
    print_formatter = logging.Formatter(fmt='[%(asctime)s][%(name)s:%(levelname)s] %(message)s')
    json_formatter = jsonlogger.JsonFormatter()

    root_logger = logging.getLogger()
    root_logger.setLevel(DATA)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO if not debug_stdout else logging.DEBUG)
    stdout_handler.setFormatter(print_formatter)
    root_logger.addHandler(stdout_handler)

    if filename:
        file_handler = logging.handlers.RotatingFileHandler(filename, maxBytes=10*1024*1024, backupCount=10)
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(DATA)
        root_logger.addHandler(file_handler)
