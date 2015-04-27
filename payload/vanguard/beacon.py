import collections
import datetime
import json
import re
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
        telemetry = self.update_stats() or dict()
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

    def read_uptime(self, path='/proc/uptime'):
        with open(path, 'r'):
            return float(f.readline().split()[0])

    def on_interval(self):
        self.send_location()
        if self.telemetry_count % self.telemetry_multiple == 0:
            self.send_telemetry()
            self.telemetry_count += 1
