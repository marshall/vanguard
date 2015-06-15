#!/usr/bin/env python
from datetime import datetime, timedelta
import json
import math
import os
import sys

class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return super(DateTimeJSONEncoder, self).default(obj)

class AndroidLog(object):
    # There were no timestamps in the STRAT-3 android log, but we know that each
    # telemetry entry is logged (approximately) every 5 seconds, giving us a basis.
    # I also recovered the timestamps from the received SMS messages using the SMS
    # app, so I use those known values as anchor points for calculating the rest of
    # the log entries
    known_timestamps = (
        ("SMS RCVD FROM 28809090", datetime(2015, 6, 7, 10, 12)),
        ("SMS RCVD FROM +1214", datetime(2015, 6, 7, 16, 29)),
    )
    timestamp = None

    def process_telemetry(self, data):
        if not self.timestamp:
            return False

        self.timestamp += timedelta(seconds=5)
        data['timestamp'] = self.timestamp
        return True

    def process_string(self, data):
        found_timestamp = False
        for ts in self.known_timestamps:
            if data['data'].startswith(ts[0]):
                self.timestamp = data['timestamp'] = ts[1]
                found_timestamp = True
                break

        if not self.timestamp:
            return False

        data['timestamp'] = self.timestamp
        return True

    def get_entries(self):
        encoder = DateTimeJSONEncoder()
        log = []
        with open(sys.argv[1], 'r') as f:
            for line in f:
                data = json.loads(line)
                if data['type'] == 'string':
                    if self.process_string(data):
                        log.append(data)
                elif data['type'] == 'telemetry':
                    if self.process_telemetry(data):
                        log.append(data)
        return log

BASE_KML = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Document>
        <name>STRAT-3 Flight Path</name>
        <Style id="yellowPoly">
            <LineStyle>
                <color>7f00ffff</color>
                <width>4</width>
            </LineStyle>
            <PolyStyle>
                <color>7f00ff00</color>
            </PolyStyle>
        </Style>
        <Placemark>
            <name>Flight path</name>
            <description>
                {flight_time_hr:0.2f} hours, {ground_distance_km:.1f} km, Avg. {avg_ground_speed_kmh:.1f} km/h
            </description>
            <styleUrl>#yellowPoly</styleUrl>
            <LineString>
                <extrude>1</extrude>
                <tesselate>1</tesselate>
                <altitudeMode>absolute</altitudeMode>
                <coordinates>
                    {flight_path}
                </coordinates>
            </LineString>
        </Placemark>
        <Placemark>
            <name>Balloon Launch</name>
            <description>{launch.date:%m/%d/%Y %H:%M:%S}</description>
            <Point><coordinates>{launch.longitude},{launch.latitude},{launch.altitude_m}</coordinates></Point>
        </Placemark>
        <Placemark>
            <name>Balloon Landing</name>
            <description>{landing.date:%m/%d/%Y %H:%M:%S}</description>
            <Point><coordinates>{landing.longitude},{landing.latitude},{landing.altitude_m}</coordinates></Point>
        </Placemark>
    </Document>
</kml>'''

FLIGHT_PATH = '{point.longitude},{point.latitude},{point.altitude_m}\n'
class Point(object):
    def __init__(self, entry):
        self.latitude = entry['data']['latitude']
        self.longitude = entry['data']['longitude']
        self.altitude = entry['data'].get('altitude', 0.3)
        self.altitude_m = self.altitude * 1000
        self.date = entry['timestamp']
        self.duration = timedelta(seconds=0)

    def __cmp__(self, p):
        return cmp(self.latitude, p.latitude) + \
               cmp(self.longitude, p.longitude) + \
               cmp(self.altitude, p.altitude)

ground_speed_kmh = {'max': 0, 'min': 0, 'avg': 0}

def calc_ground_speed(point1, point2):
    km = haversine_distance(point1.latitude, point1.longitude,
                            point2.latitude, point2.longitude)

    time = (point2.date - point1.date).total_seconds()

    kmh = km / (time / 3600.0)
    ground_speed_kmh['min'] = min(kmh, ground_speed_kmh['min'])
    ground_speed_kmh['max'] = max(kmh, ground_speed_kmh['max'])

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371 #km
    dLat = math.radians(lat2-lat1)
    dLon = math.radians(lon2-lon1)
    lat1 = math.radians(lat1)
    lat2 = math.radians(lat2)

    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = R * c
    return d

def main():
    entries = AndroidLog().get_entries()
    last = -1
    first = -1

    # These were reverse engineered by trial and error :(
    first_long = -97.30647558307501
    first_lat = 33.24347828714187
    for i in range(len(entries)):
        e = entries[i]
        if e['type'] == 'string' and \
           e['data'].startswith('SMS RCVD FROM +1214') and \
           ': Location' in e['data']:
           last = i
        elif e['type'] == 'telemetry' and \
             e['data']['longitude'] == first_long and \
             e['data']['latitude'] == first_lat:
          first = i

    def entry_filter(e):
        return e['type'] == 'telemetry' and \
               e['data']['latitude'] != 0 and e['data']['longitude'] != 0

    log = filter(entry_filter, entries[first:last])
    last_point = None
    last_entry = None

    # reduce entries with the same lat/lon to 1 entry
    reduced_log = []
    for entry in log:
        point = Point(entry)
        if last_point and point.latitude == last_point.latitude \
                      and point.longitude == last_point.longitude:

            continue
        reduced_log.append(point)
        last_point = point

    flight_path = ''
    launch = None
    burst = None
    landing = None

    found_burst = False
    found_landing = False

    i = 0
    for point in reduced_log:
        if i == 0:
            launch = point
        else:
            landing = point

        flight_path += FLIGHT_PATH.format(point=point)
        if last_point:
            calc_ground_speed(last_point, point)

        last_point = point
        i += 1

    ground_distance_km = haversine_distance(launch.latitude, launch.longitude,
                                            landing.latitude, landing.longitude)
    flight_time = (landing.date - launch.date).total_seconds()

    ground_speed_kmh['avg'] = ground_distance_km / (flight_time / 3600.0)

    print BASE_KML.format(flight_path=flight_path,
                          launch=launch,
                          landing=landing,
                          ground_distance_km=ground_distance_km,
                          avg_ground_speed_kmh=ground_speed_kmh['avg'],
                          flight_time_hr=flight_time/3600.0)

if __name__ == '__main__':
    main()
