import binascii
import datetime
import logging
import json
import time

import afsk, afsk.ax25
import dateutil.parser
import kiss
import redis
import socket

import proto
import os
import sys
import subprocess

from command import command
from looper import Interval

@command('beacon')
class Beacon(Interval):
    # location_fmt = '/{time}h{location}O{course:03.0f}/{speed:03.0f}/A={alt:06.0f}'
    # telemetry_fmt = 'T#{packet_id:03d},{r1:03d},{r2:03d},{r3:03d},{r4:03d},{r5:03d},{d:08b}'

    def __init__(self, config):
        super(Beacon, self).__init__(interval=config.beacon.position_interval)
        self.beacon = config.beacon
        self.telemetry_multiple = config.beacon.telemetry_interval / \
                                  config.beacon.position_interval
        self.redis = redis.StrictRedis()
        self.telemetry_count = 0
        self.radios = []

        if 'uart' in self.beacon:
            import Adafruit_BBIO.UART as UART
            UART.setup(self.beacon.uart)

        if 'radio_uart' in self.beacon:
            from xtend900 import Xtend900
            radio = Xtend900(device=self.beacon.radio_device,
                             baudrate=self.beacon.radio_baudrate,
                             uart=self.beacon.radio_uart)
            radio.connect()
            self.radios.append(radio)

        if 'tnc_device' in self.beacon:
            tnc = kiss.KISS(self.beacon.tnc_device, self.beacon.tnc_baudrate)
            tnc.start()
            self.radios.append(tnc)

    # def format_latlon_dm(self, dd, type='lat'):
    #     is_positive = dd >= 0
    #     degrees = abs(int(dd))
    #     minutes = abs(int(dd) - dd) * 60

    #     if type == 'lat': # latitude
    #         suffix = 'N' if is_positive else 'S'
    #         degrees_fmt = '%02d'
    #     else: # longitude
    #         suffix = 'E' if is_positive else 'W'
    #         degrees_fmt = '%03d'

    #     return ''.join([degrees_fmt % degrees, '%05.2f' % minutes, suffix])

    # def send_packet(self, packet):
    #     self.log.info('SEND %s', packet)
    #     digis = (bytes(digi) for digi in self.beacon.path.split(','))
    #     ax25_packet = afsk.ax25.UI(source=self.beacon.callsign,
    #                                digipeaters=digis,
    #                                info=bytes(packet))

    #     frame = b'{header}{info}'.format(
    #         flag=ax25_packet.flag,
    #         header=ax25_packet.header(),
    #         info=ax25_packet.info,
    #         fcs=ax25_packet.fcs())

    #     self.log.debug('AX.25 frame: %s', binascii.hexlify(frame))
    #     for radio in self.radios:
    #         try:
    #             radio.write(frame)
    #         except socket.timeout, e:
    #             self.log.error('serial write timeout')

    def send_message(self, msg, src='beacon', **kwargs):
        if not isinstance(msg, proto.Msg):
            msg = msg.from_data(**kwargs)

        self.log.message(msg)

        for radio in self.radios:
          try:
              radio.write(frame)
          except socket.timeout, e:
              self.log.error('serial write timeout')


    def send_location(self, lat=0.0, lon=0.0, alt=0.0, track=0.0, speed=0.0, time=0.0, **kwargs):
         self.send_message(proto.LocationMsg,
                          latitude=lat,
                          longitude=lon,
                          altitude=alt,
                          #quality=self.gps.quality,
                          #satellites=self.gps.satellites,
                          speed=speed)



    def send_telemetry(self, **kwargs):
        self.send_message(proto.TelemetryMsg,
                          uptime=int(kwargs.get("uptime")),
                          mode=0,
                          cpu_usage=int(kwargs.get("cpu_usage")),
                          free_mem=int(kwargs.get("free_mem")/1024),
                          int_temperature=kwargs.get("int_temp",0),
                          int_humidity=0,
                          ext_temperature=kwargs.get("ext_temp",0))
        self.redis.incr('telemetry') 

    def collect_telemetry(self):
        telemetry = dict()
        stats = self.update_stats()
        if stats:
            telemetry.update(stats)

        data = self.redis.lindex('temps', -1)
        if data:
            temps = json.loads(data)
            telemetry['int_temp'] = temps['int']

        self.send_telemetry(**telemetry)

    def on_interval(self):
        data = self.redis.lindex('locations', -1)
        if not data:
            return

        location = json.loads(data)
        self.send_location(**location)

        if self.telemetry_count % self.telemetry_multiple == 0:
            self.collect_telemetry()
            self.telemetry_count += 1

    def update_stats(self):
        try:
            sys_helper = os.path.join(os.path.dirname(__file__), 'sys_helper.sh')
            result = subprocess.check_output([sys_helper, 'get_stats'])
            return json.loads(result)
        except subprocess.CalledProcessError, e:
            return None
