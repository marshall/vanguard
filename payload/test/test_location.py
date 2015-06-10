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

this_dir = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(this_dir)
sys.path.append(top_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('location-test')

class GpsFake(threading.Thread):
    def __init__(self):
        super(GpsFake, self).__init__(name='GpsFake')
        self.proc = None

    def run(self):
        gps_log = os.path.join(this_dir, 'gps.log')
        cmd = ['gpsfake', '-u', '-c', '0.01', gps_log]
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
        from vanguard import location, config
        l = location.Location(config.Config())
        while not l.ensure_connected():
            pass

        while l.redis.llen('location') == 0:
            l.on_iteration()

        loc = l.redis.lindex('location', -1)
        self.assertTrue(loc is not None)
        self.assertEqual(l.redis.get('location_session_count'), '1')

        data = json.loads(loc)
        self.assertTrue(data['lat'] != 0)
        self.assertTrue(data['lon'] != 0)

    def tearDown(self):
        self.gpsfake.stop()
