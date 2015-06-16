import json
import logging
import os
import sys
import unittest

import mock
import mockredis
from pexif import JpegFile

this_dir = os.path.dirname(os.path.abspath(__file__))
top_dir = os.path.dirname(this_dir)
sys.path.append(top_dir)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('camera-test')

class TestCamera(unittest.TestCase):
    def setUp(self):
        from vanguard import config

        self.config = config.Config(data=dict(
            work_dir='/tmp',
            camera=dict(
                device='/tmp',
                resolution='RESOLUTION',
                quality=100,
                depth=24,
                interval=15
            ),
            programs=dict(
                streamer=os.path.join(this_dir, 'mock_streamer.py'))))

    @mock.patch('redis.StrictRedis', mockredis.mock_strict_redis_client)
    def test_camera(self):
        from vanguard import camera
        c = camera.Camera(self.config)
        c.redis.rpush('location', '{"lat": 22, "lon": 33, "alt": 44}')
        c.redis.rpush('telemetry', '{"int_temp": 22, "ext_temp": 33}')
        c.on_interval()

        self.assertEqual(c.redis.llen('photos'), 1)
        photo = c.redis.lindex('photos', -1)
        self.assertEqual(photo, '/tmp/photos/00000.jpeg')

        jpeg = JpegFile.fromFile(photo)
        lat, lon = jpeg.get_geo()
        self.assertEqual(lat, 22.0)
        self.assertEqual(lon, 33.0)
        self.assertEqual(jpeg.exif.primary.GPS.GPSAltitudeRef, ['\x00'])
        self.assertEqual(jpeg.exif.primary.GPS.GPSAltitude[0].as_tuple(), (44, 1))

        telemetry = json.loads(''.join(jpeg.exif.primary.ExtendedEXIF.UserComment))
        self.assertEqual(telemetry['int_temp'], 22)
        self.assertEqual(telemetry['ext_temp'], 33)
