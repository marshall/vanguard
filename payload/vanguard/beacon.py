import collections
import datetime
import json
import time

import redis
import socket

import os
import sys
import subprocess

from command import command
from looper import Interval
from radio import Radio

@command('beacon')
class Beacon(Interval):
    def __init__(self, config):
        super(Beacon, self).__init__(interval=config.beacon.position_interval)
        self.beacon = config.beacon
        self.telemetry_multiple = config.beacon.telemetry_interval / \
                                  config.beacon.position_interval
        self.redis = redis.StrictRedis()
        self.telemetry_count = 0
        self.radios = collections.OrderedDict({})

        for key, radio_config in config.radios.iteritems():
            self.radios[key] = Radio(**radio_config)

    def send_location(self):
        data = self.redis.lindex('locations', -1)
        if not data:
            return

        location = json.loads(data)
        for name, radio in self.radios.iteritems():
            radio.send_location(**location)

    def send_telemetry(self):
        telemetry = dict()
        stats = self.update_stats()
        if stats:
            telemetry.update(stats)

        data = self.redis.lindex('temps', -1)
        if data:
            temps = json.loads(data)
            telemetry['int_temp'] = temps.get('int', 0)
            telemetry['ext_temp'] = temps.get('ext', 0)

        packet_id = self.redis.get('telemetry') or 0
        for name, radio in self.radios.iteritems():
            radio.send_telemetry(packet_id, **telemetry)

        self.redis.incr('telemetry')

    def update_stats(self):
        try:
            sys_helper = os.path.join(os.path.dirname(__file__), 'sys_helper.sh')
            result = subprocess.check_output([sys_helper, 'get_stats'])
            return json.loads(result)
        except subprocess.CalledProcessError, e:
            return None

    def on_interval(self):
        self.send_location()
        if self.telemetry_count % self.telemetry_multiple == 0:
            self.send_telemetry()
            self.telemetry_count += 1
