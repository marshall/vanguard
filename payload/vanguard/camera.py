#!/usr/bin/env python
import json
import os
import subprocess
import sys
import time

import redis
from pexif import JpegFile

from command import command
from looper import Interval

@command('camera')
class Camera(Interval):
    def __init__(self, config):
        super(Camera, self).__init__(interval=config.camera.interval)
        self.photo_dir = os.path.join(config.work_dir, 'photos')
        if not os.path.exists(self.photo_dir):
            os.makedirs(self.photo_dir)

        self.camera = config.camera
        self.redis = redis.StrictRedis()

    def geotag_photo(self, filename):
        if not self.redis.exists('locations'):
            return

        location = json.loads(self.redis.lindex('locations', -1))

        try:
            self.log.info('geotag %s (%f, %f)', filename,
                          location['lat'], location['lon'])
            jpeg = JpegFile.fromFile(filename)
            jpeg.set_geo(location['lat'], location['lon'])
            jpeg.writeFile(filename)
        except (IOError, JpegFile.InvalidFile):
            self.log.exception('Error geotagging photo: %s', filename)

    def on_interval(self):
        filename = os.path.join(self.photo_dir,
                                '%05d.jpeg' % self.redis.llen('photos'))

        cmd = [self.camera['streamer'],
               self.camera['device'],
               '-s', self.camera['resolution'],
               '-j', str(self.camera['quality']),
               '-b', str(self.camera['depth']),
               '-o', filename]
        try:
            self.log.info(" ".join(cmd))
            subprocess.check_call(cmd)
            self.redis.rpush('photos', filename)
            self.geotag_photo(filename)
        except subprocess.CalledProcessError, e:
            self.log.error('Failed to call streamer: %s', str(e))

if __name__ == '__main__':
    Camera().main()
