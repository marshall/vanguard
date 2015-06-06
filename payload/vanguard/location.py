import errno
import json
import socket
import time

import gps
import redis

from command import command
from looper import Looper

@command('location')
class Location(Looper):
    host = 'localhost'
    port = 2947
    reconnect_timeout = 0.5

    def __init__(self, config):
        super(Location, self).__init__()
        self.gps = config.gps
        self.redis = redis.StrictRedis()
        self.session = None

    def ensure_connected(self):
        if not self.session:
            try:
                self.session = gps.gps(self.host, self.port,
                                       mode=gps.WATCH_ENABLE|gps.WATCH_NEWSTYLE)
                self.redis.set('location_session_count', 0)
            except socket.error, e:
                if self.session:
                    self.session.close()
                    self.session = None

        return self.session

    def record_location(self, report):
        location = dict(lat=report.get('lat', 0),
                        lon=report.get('lon', 0),
                        alt=report.get('alt', 0),
                        speed=report.get('speed', 0),
                        climb=report.get('climb', 0),
                        time=report.get('time', time.time()),
                        localtime=time.time())

        location_str = json.dumps(location)
        self.redis.rpush('location', location_str)
        self.redis.incr('location_session_count')

    def on_stopped(self):
        self.log.info('gpsd has terminated')

    def on_iteration(self):
        if not self.ensure_connected():
            self.log.warn('Failed to connect to gpsd, will try again in %f seconds',
                          self.reconnect_timeout)
            time.sleep(self.reconnect_timeout)
            self.reconnect_timeout *= 2
            return

        report = self.session.next()

        report_class = report.get('class')
        if report_class == 'TPV':
            tag = report.get('tag')
            if tag == 'GGA': # fix
                self.record_location(report)

    def on_cleanup(self):
        if self.session:
            self.session.close()
            self.session = None

        self.log.info('gpsd has terminated')
