import json
import logging
import os
import subprocess
import sys
import threading
import time
import unittest

import mock
import mockredis

this_dir = os.path.abspath(os.path.dirname(__file__))
vanguard_dir = os.path.abspath(os.path.join(this_dir, '..', 'vanguard'))
sys.path.append(vanguard_dir)

import config
import location

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('location-test')

class GpsFake(threading.Thread):
    def __init__(self):
        super(GpsFake, self).__init__(name='GpsFake')
        self.proc = None

    def run(self):
        gps_log = os.path.join(this_dir, 'gps.log')
        cmd = ['gpsfake', '-c', '0.1', gps_log]
        logger.info(cmd)

        self.proc = subprocess.Popen(cmd)
        self.proc.communicate()

    def stop(self):
        self.proc.terminate()
        self.proc = None

class LocationTest(unittest.TestCase):
    def setUp(self):
        self.gpsfake = GpsFake()
        self.gpsfake.start()

    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def test_location(self):
        l = location.Location(config.Config())
        while not l.ensure_connected():
            pass

        l.on_iteration() # VERSION
        l.on_iteration() # DEVICES
        l.on_iteration() # WATCH
        l.on_iteration() # DEVICE
        l.on_iteration() # first lock

        self.assertEqual(l.redis.llen('locations'), 1)
        loc = l.redis.lindex('locations', -1)
        self.assertTrue(loc is not None)

        data = json.loads(loc)
        self.assertTrue(data['lat'] > 0)
        self.assertTrue(data['lon'] > 0)

    def tearDown(self):
        self.gpsfake.stop()
