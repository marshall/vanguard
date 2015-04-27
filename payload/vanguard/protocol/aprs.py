import datetime

import afsk, afsk.ax25
import dateutil.parser

class APRSFormatter(object):
    POSITION  = '/{time}h{location}O{course:03.0f}/{speed:03.0f}/A={alt:06.0f}'
    TELEMETRY = 'T#{packet_id:03d},{r1:03d},{r2:03d},{r3:03d},{r4:03d},{r5:03d},{d:08b}'

    def __init__(self, **kwargs):
        self.aprs_path = kwargs.get('aprs_path', 'APRS,TCPIP*')
        self.callsign = kwargs.get('callsign', 'N0CALL')

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

    def format_location(self, lat=0.0, lon=0.0, alt=0.0, time=0, speed=0, track=0,
                        **kwargs):
        lat_dm = self.format_latlon_dm(lat)
        lon_dm = self.format_latlon_dm(lon, type='lon')

        if isinstance(time, (int, float)):
            time = datetime.datetime.fromtimestamp(float('time'))
        else:
            time = dateutil.parser.parse(time)

        speed_kmh = (speed / 1000.0) * 3600.0 # meters/sec -> km/hour
        alt_feet = alt * 3.28084

        return self.POSITION.format(time=time.strftime('%H%M%S'),
                                    location='/'.join([lat_dm, lon_dm]),
                                    course=track,
                                    speed=speed_kmh,
                                    alt=alt_feet)

    def format_telemetry(self, packet_id, int_temp=0, ext_temp=0, **kwargs):
        return self.TELEMETRY.format(packet_id=int(packet_id),
                                     r1=int(int_temp),
                                     r2=int(ext_temp),
                                     r3=0,
                                     r4=0,
                                     r5=0,
                                     d=0) # r3-r5,d are unused for now

    def format_packet(self, data):
        digis = (bytes(digi) for digi in self.aprs_path.split(','))
        ax25_packet = afsk.ax25.UI(source=self.callsign,
                                   digipeaters=digis,
                                   info=bytes(data))

        return b'{header}{info}'.format(flag=ax25_packet.flag,
                                        header=ax25_packet.header(),
                                        info=ax25_packet.info,
                                        fcs=ax25_packet.fcs())
