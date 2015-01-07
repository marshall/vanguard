import datetime
import json

import dateutil.parser
import redis
import serial
import socket

from command import command
from looper import Interval

@command('beacon')
class Beacon(Interval):
    packet_fmt   = '{callsign}>APRS,{path}:{text}'
    location_fmt = '/{time}h{location}O{course:03.0f}/{speed:03.0f}/A={alt:06.0f}'
    telemetry_fmt = 'T#{packet_id:03d},{r1:03d},{r2:03d},{r3:03d},{r4:03d},{r5:03d},{d:08b}'

    def __init__(self, config):
        super(Beacon, self).__init__(interval=config.beacon.interval)
        self.beacon = config.beacon
        self.redis = redis.StrictRedis()
        self.telemetry_count = 0

        if 'uart' in self.beacon:
            import Adafruit_BBIO.UART as UART
            UART.setup(self.beacon.uart)

    def format_packet(self, text):
        return self.packet_fmt.format(text=text, **self.beacon)

    def format_latlon_dm(self, dd, type='lat'):
        is_positive = dd >= 0
        degrees = abs(int(dd))
        minutes = abs(int(dd) - dd) * 60

        if type == 'lat': # latitude
            suffix = 'N' if is_positive else 'S'
            degrees_fmt = '%02d'
        else: # longitude
            suffix = 'E' if is_positive else 'W'
            degrees_fmt = '%03d'

        return ''.join([degrees_fmt % degrees, '%05.2f' % minutes, suffix])

    def send_packet(self, packet):
        self.log.info('SEND %s', packet)
        try:
            ser = serial.Serial(self.beacon.device, self.beacon.baudrate, timeout=1)
            ser.write(packet)
            ser.close()
        except socket.timeout, e:
            self.log.error('serial write timeout')

    def send_location(self, lat=0.0, lon=0.0, alt=0.0, track=0.0, speed=0.0, time=0.0, **kwargs):
        lat_dm = self.format_latlon_dm(lat)
        lon_dm = self.format_latlon_dm(lon, type='lon')

        if isinstance(time, (int, float)):
            time = datetime.datetime.fromtimestamp(float(time))
        else:
            time = dateutil.parser.parse(time)

        speed_kmh = (speed / 1000.0) * 3600.0 # meters/sec -> km/hour
        alt_feet = alt * 3.28084

        packet = self.location_fmt.format(
                   time=time.strftime('%H%M%S'),
                   location='/'.join([lat_dm, lon_dm]),
                   course=track,
                   speed=speed_kmh,
                   alt=alt_feet)

        self.send_packet(self.format_packet(packet))

    def send_telemetry(self, int_temp=0.0, ext_temp=0.0):
        packet_id = self.redis.get('telemetry') or 0
        packet = self.telemetry_fmt.format(
                packet_id=int(packet_id),
                r1=int(int_temp),
                r2=int(ext_temp),
                r3=0, r4=0, r5=0, d=0) # the rest of the readings are unused for now

        self.send_packet(self.format_packet(packet))
        self.redis.incr('telemetry')

    def on_interval(self):
        data = self.redis.lindex('locations', -1)
        if not data:
            return

        location = json.loads(data)
        self.send_location(**location)

        if self.telemetry_count % 4 == 0:
            data = self.redis.lindex('temps', -1)
            if data:
                temps = json.loads(data)
                self.send_telemetry(int_temp=temps['int'])
        self.telemetry_count += 1

