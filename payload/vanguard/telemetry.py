import json
import math
import re
import sys
import time

import Adafruit_BBIO.ADC as ADC
import redis

from command import command
from looper import Interval

@command('telemetry')
class Telemetry(Interval):
    REF_VOLTAGE           = 3300    # reference voltage in millivolts
    SERIAL_RESISTOR       = 10000
    BCOEFFICIENT          = 3950
    THERMISTOR_NOMINAL    = 10000
    KELVIN_TO_C           = 273.15
    TEMPERATURE_NOMINAL_K = 25 + KELVIN_TO_C

    def __init__(self, config):
        super(Telemetry, self).__init__(interval=config.telemetry.interval)
        self.telemetry = config.telemetry
        self.redis = redis.StrictRedis()

        ADC.setup()

    def calc_temp(self, pin):
        value = ADC.read(pin)
        if value == 0:
            return 0

        reading = self.SERIAL_RESISTOR / value
        steinhart = reading / self.THERMISTOR_NOMINAL #  (R/Ro)
        steinhart = math.log(steinhart)               #  ln(R/Ro)
        steinhart /= self.BCOEFFICIENT                #  1/B * ln(R/Ro)
        steinhart += 1.0 / self.TEMPERATURE_NOMINAL_K # + (1/To)
        return (1.0 / steinhart) - self.KELVIN_TO_C   #  Invert, convert to C

    def update_stats(self):
        stats = dict()
        with open('/proc/uptime', 'r') as f:
            lines = f.read().splitlines()
            stats['uptime'] = float(lines[0].split()[0])

        with open('/proc/stat', 'r') as f:
            # usr nice sys idle iowait irq guest
            for line in f.read().splitlines():
                tokens = re.split(r' +', line.strip())
                if tokens[0] != 'cpu':
                    continue

                usr, nice, sys, idle, iowait = map(float, tokens[1:6])
                active = usr + sys + iowait
                total = active + idle
                percent = active * 100 / total
                stats['cpu_usage'] = int(percent)
                break

        with open('/proc/meminfo', 'r') as f:
            meminfo = dict()
            for line in f.read().splitlines():
                tokens = re.split(r'[: ]+', line.strip())
                meminfo[tokens[0]] = tokens[1]

            if 'MemFree' in meminfo:
                stats['free_mem'] = int(meminfo['MemFree'])

        return stats

    def on_interval(self):
        now = time.time()
        telemetry = self.update_stats() or dict()
        int_temp = ext_temp = 0

        if 'int_temp_pin' in self.telemetry:
            int_temp = self.calc_temp(self.telemetry.int_temp_pin)

        if 'ext_temp_pin' in self.telemetry:
            ext_temp = self.calc_temp(self.telemetry.ext_temp_pin)


        telemetry['int_temp'] = int_temp
        telemetry['ext_temp'] = ext_temp

        telemetry_str = json.dumps(telemetry)
        self.log.info(telemetry_str)
        self.redis.rpush('telemetry', telemetry_str)
