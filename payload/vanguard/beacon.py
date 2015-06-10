import collections
import datetime
import json
import re
import threading
import time

import redis
import socket

import os
import sys
import subprocess

from command import command
from looper import Looper
from radio import Radio
from handler import *

@command('beacon')
class Beacon(Looper):
    handler_types = [PingHandler, UploadHandler]

    def __init__(self, config):
        super(Beacon, self).__init__()
        self.interval = config.beacon.interval
        self.beacon = config.beacon
        self.redis = redis.StrictRedis()
        self.radios = collections.OrderedDict({})

        self.handlers = [handler() for handler in self.handler_types]
        for key, radio_config in config.radios.iteritems():
            self.radios[key] = Radio(**radio_config)

        self.recv_timeout = self.interval / len(self.radios)

    def last_entry(self, redis_key):
        list_len = self.redis.llen(redis_key)
        entry = self.redis.lindex(redis_key, list_len - 1)
        if list_len == 0 or not entry:
            self.log.warn('Bad last entry for %s' % redis_key)
            return None

        try:
            e = json.loads(entry)
            e['_index'] = list_len - 1
            return e
        except:
            self.log.exception('Error parsing redis %s JSON' % redis_key)
            return None

    def send_last_entry(self, key):
        entry = self.last_entry(key)
        if not entry:
            return

        for name, radio in self.radios.iteritems():
            radio.send(key, **entry)

    def handle_packet(self, radio, packet):
        # Vanguard message received from ground station
        for handler in self.handlers:
            if handler.msg_type == packet.msg_type:
                handler.handle(radio, packet)
                break

    def on_started(self):
        for radio in self.radios.values():
            radio.start()


    def recv_data(self):
        for radio in self.radios.values():
            packet = radio.recv(self.recv_timeout)
            if packet:
                self.handle_packet(radio, packet)

    def on_iteration(self):
        self.recv_data()
        self.send_last_entry('location')
        self.send_last_entry('telemetry')
