#!/usr/bin/env python
import json
import os
import struct
import subprocess
import sys
import time

import redis
from pexif import JpegFile, Rational

from command import command
from looper import Interval

@command('camera')
class Camera(Interval):
    def __init__(self, config):
        super(Camera, self).__init__(interval=config.camera.interval)
        self.photo_dir = os.path.join(config.work_dir, 'photos')
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

        self.streamer = config.programs.streamer
        self.camera = config.camera
        self.redis = redis.StrictRedis()
        self.proc = None

        if not os.path.exists(config.camera.device):
            self.log.warn('Camera @ %s does not exist, waiting.', config.camera.device)

    def tag_photo(self, filename):
        location_str = self.redis.lindex('location', -1)
        telemetry_str = self.redis.lindex('telemetry', -1)
        location = json.loads(location_str) if location_str else None
        telemetry = json.loads(telemetry_str) if telemetry_str else None

        if not (location or telemetry):
            return

        try:
            jpeg = JpegFile.fromFile(filename)
            attr = jpeg.get_exif(create=True).get_primary(create=True)
            self.log.info('tag %s' % filename, extra={'location': location,
                                                      'telemetry': telemetry})
            if location:
                jpeg.set_geo(location['lat'], location['lon'])

                attr.GPS.GPSAltitudeRef = '\x00' # Above sea level
                attr.GPS.GPSAltitude = [Rational(int(location['alt']), 1)]

            if telemetry:
                attr.ExtendedEXIF.UserComment = telemetry_str

            jpeg.writeFile(filename)
        except (IOError, JpegFile.InvalidFile):
            self.log.exception('Error tagging photo: %s', filename)

    def on_interval(self):
        if not os.path.exists(self.camera.device):
            return

        filename = os.path.join(self.photo_dir,
                                '%05d.jpeg' % self.redis.llen('photos'))

        cmd = [self.streamer,
               self.camera.device,
               '-s', self.camera.resolution,
               '-j', str(self.camera.quality),
               '-b', str(self.camera.depth),
               '-o', filename]

        self.log.info(" ".join(cmd))
        self.proc = subprocess.Popen(cmd)
        result = self.proc.wait()

        if result != 0:
            self.log.error('streamer call failed: %d', result)
            return

        self.redis.rpush('photos', filename)
        self.tag_photo(filename)

    def on_cleanup(self):
        if self.proc:
            self.proc.terminate()
            self.proc = None

if __name__ == '__main__':
    Camera().main()
