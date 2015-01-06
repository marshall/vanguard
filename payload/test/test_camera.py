import json
import logging
import os
import sys
import unittest

import mock
import mockredis
from pexif import JpegFile

this_dir = os.path.abspath(os.path.dirname(__file__))
vanguard_dir = os.path.abspath(os.path.join(this_dir, '..', 'vanguard'))
sys.path.append(vanguard_dir)

import config
import camera

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('camera-test')

class TestCamera(unittest.TestCase):
    def setUp(self):
        self.config = config.Config(data=dict(
            work_dir='/tmp',
            camera=dict(
                device='DEVICE',
                resolution='RESOLUTION',
                quality=100,
                depth=24,
                interval=15,
                streamer=os.path.join(this_dir, 'mock_streamer.py')
            )))

    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def test_camera(self):
        c = camera.Camera(self.config)
        c.redis.rpush('locations', '{"lat": 22, "lon": 33, "alt": 44}')
        c.on_interval()

        self.assertEqual(c.redis.llen('photos'), 1)
        photo = c.redis.lindex('photos', -1)
        self.assertEqual(photo, '/tmp/photos/00000.jpeg')

        jpeg = JpegFile.fromFile(photo)
        lat, lon = jpeg.get_geo()
        self.assertEqual(lat, 22.0)
        self.assertEqual(lon, 33.0)
