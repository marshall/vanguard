import json
import time
import math
import sys

import Adafruit_BBIO.ADC as ADC
import redis

from command import command
from looper import Interval

@command('temp')
class Temp(Interval):
    REF_VOLTAGE           = 3300    # reference voltage in millivolts
    SERIAL_RESISTOR       = 10000
    BCOEFFICIENT          = 3950
    THERMISTOR_NOMINAL    = 10000
    KELVIN_TO_C           = 273.15
    TEMPERATURE_NOMINAL_K = 25 + KELVIN_TO_C

    def __init__(self, config):
        super(Temp, self).__init__(interval=config.temp.interval)
        self.temp = config.temp
        self.redis = redis.StrictRedis()

        ADC.setup()

    def calc_temp(self, pin):
        value = ADC.read(pin)
        reading = self.SERIAL_RESISTOR / value
        self.log.info('Value: %f, Thermistor resistance: %f', value, reading)

        steinhart = reading / self.THERMISTOR_NOMINAL #  (R/Ro)
        steinhart = math.log(steinhart)               #  ln(R/Ro)
        steinhart /= self.BCOEFFICIENT                #  1/B * ln(R/Ro)
        steinhart += 1.0 / self.TEMPERATURE_NOMINAL_K # + (1/To)
        return (1.0 / steinhart) - self.KELVIN_TO_C   #  Invert, convert to C

    def on_interval(self):
        now = time.time()
        int_temp = ext_temp = 0

        if 'int_temp_pin' in self.temp:
            int_temp = self.calc_temp(self.temp.int_temp_pin)

        if 'ext_temp_pin' in self.temp:
            ext_temp = self.calc_temp(self.temp.ext_temp_pin)

        self.log.info('temp. internal: %.1f, external: %.1f', int_temp, ext_temp)

        self.redis.rpush('temps', json.dumps({
            'int': int_temp,
            'ext': ext_temp,
            'time': now
        }))
