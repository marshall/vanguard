import argparse
import collections
import json
import logging
import math
import os
import sys

logger = logging.getLogger('burstcalc')
logging.basicConfig(level=logging.INFO)

class Preset(object):
    def __init__(self, manufacturer, mass, burst_diameter, cd=0.25):
        self.manufacturer = manufacturer
        self.mass = mass
        self.burst_diameter = burst_diameter
        self.cd = cd

gas_densities = dict(he=0.1786, h=0.0899, ch4=0.6672)
balloons = dict(k200=Preset('Kaymont', 200, 3.00),
                k300=Preset('Kaymont', 300, 3.78),
                k350=Preset('Kaymont', 350, 4.12),
                k450=Preset('Kaymont', 450, 4.72),
                k500=Preset('Kaymont', 500, 4.99),
                k600=Preset('Kaymont', 600, 6.02, cd=0.30),
                k700=Preset('Kaymont', 700, 6.53, cd=0.30),
                k800=Preset('Kaymont', 800, 7.00, cd=0.30),
                k1000=Preset('Kaymont', 1000, 7.86, cd=0.30),
                k1200=Preset('Kaymont', 1200, 8.63),
                k1500=Preset('Kaymont', 1500, 9.44),
                k2000=Preset('Kaymont', 2000, 10.54),
                k3000=Preset('Kaymont', 3000, 13.00),
                # 100g Hwoyee Data from http://www.hwoyee.com/images.aspx?fatherId=11010101&msId=1101010101&title=0,
                h100=Preset('Hwoyee', 100, 2.00),
                # Hwoyee data from http://www.hwoyee.com/base.asp?ScClassid=521&id=521102,
                h200=Preset('Hwoyee', 200, 3.00),
                h300=Preset('Hwoyee', 300, 3.80),
                h350=Preset('Hwoyee', 350, 4.10),
                h400=Preset('Hwoyee', 400, 4.50),
                h500=Preset('Hwoyee', 500, 5.00),
                h600=Preset('Hwoyee', 600, 5.80, cd=0.30),
                h750=Preset('Hwoyee', 750, 6.50, cd=0.30),
                h800=Preset('Hwoyee', 800, 6.80, cd=0.30),
                h950=Preset('Hwoyee', 950, 7.20, cd=0.30),
                h1000=Preset('Hwoyee', 1000, 7.50, cd=0.30),
                h1200=Preset('Hwoyee', 1200, 8.50),
                h1500=Preset('Hwoyee', 1500, 9.50),
                h1600=Preset('Hwoyee', 1600, 10.50),
                h2000=Preset('Hwoyee', 2000, 11.00),
                h3000=Preset('Hwoyee', 3000, 12.50),
                # PAWAN data from,
                # http://randomaerospace.com/Random_Aerospace/Balloons.html,
                p100=Preset('Pawan', 100, 1.6),
                p350=Preset('Pawan', 250, 4.0),
                p600=Preset('Pawan', 600, 5.8, cd=0.30),
                p800=Preset('Pawan', 800, 6.6, cd=0.30),
                p900=Preset('Pawan', 900, 7.0, cd=0.30),
                p1200=Preset('Pawan', 1200, 8.0),
                p1600=Preset('Pawan', 1600, 9.5),
                p2000=Preset('Pawan', 2000, 10.2))

def calc_burst(payload_mass=1000, # grams
               balloon_mass=1000, # grams
               target_burst_alt=0, # meters
               target_ascent_rate=0,  # m / s
               gas_density=0.1786, # kg / m^3
               air_density=1.2050, # kg / m^3
               air_density_model=7238.3,
               grav_accel=9.80665, # m / s^2
               burst_diameter=7.86, # meters
               balloon_cd=0.3):

    if target_burst_alt == 0 and target_ascent_rate == 0:
        raise Exception('Either target_burst_alt or target_ascent_rate needs to be provided')

    #ascent_rate = burst_altitude = time_to_burst = neck_lift = 0
    #launch_radius = launch_volume = 0

    payload_mass /= 1000.0
    balloon_mass /= 1000.0

    burst_volume = (4 / 3.0) * math.pi * math.pow(burst_diameter / 2.0, 3)
    if target_burst_alt > 0:
        launch_volume = burst_volume * math.exp((-target_burst_alt) / air_density_model)
        launch_radius = math.pow((3 * launch_volume) / (4 * math.pi), 1 / 3.0)
    else:
        a = grav_accel * (air_density - gas_density) * (4.0 / 3.0) * math.pi
        b = -0.5 * math.pow(target_ascent_rate, 2) * balloon_cd * air_density * math.pi
        c = 0
        d = - (payload_mass + balloon_mass) * grav_accel

        f = (((3 * c) / a) - (math.pow(b, 2) / math.pow(a, 2)) / 3.0)
        g = (((2 * math.pow(b, 3)) / math.pow(a, 3)) - \
             ((9 * b * c) / (math.pow(a, 2))) + ((27 * d) / a) / 27.0)
        h = (math.pow(g, 2) / 4.0) + (math.pow(f, 3) / 27.0)

        if h > 0:
            R = (-0.5 * g) + math.sqrt(h)
            S = math.pow(R, 1 / 3.0)
            T = (-0.5 * g) - math.sqrt(h)
            U = math.pow(T, 1.0/3.0)
            launch_radius = (S + U) - (b / (3 * a))
        elif f == 0 and g == 0 and h == 0:
            launch_radius = -1 * math.pow(d / a, 1 / 3.0)
        elif h <= 0:
            i = math.sqrt((math.pow(g, 2) / 4.0) - h)
            j = math.pow(i, 1 / 3.0)
            k = math.acos(-g / (2 * i))
            L = -1 * j
            M = math.cos(K / 3.0)
            N = math.sqrt(3) * math.sin(K / 3.0)
            P = (b / (3 * a)) * -1
            r1 = 2 * j * math.cos(k / 3.0) - (b / (3 * a))
            r2 = L * (M + N) + P
            r3 = L * (M - N) + P

            logger.warn('3 possible solutions found: %f, %f, %f', r1, r2, r3)

            if r1 > 0:
                launch_radius = r1
            elif r2 > 0:
                launch_radius = r2
            elif r3 > 0:
                launch_radius = r3

    launch_area = math.pi * math.pow(launch_radius, 2)
    launch_volume = (4 / 3.0) * math.pi * math.pow(launch_radius, 3)
    density_diff = air_density - gas_density
    gross_lift = launch_volume * density_diff
    neck_lift = (gross_lift - balloon_mass) * 1000
    total_mass = payload_mass + balloon_mass
    free_lift = (gross_lift - total_mass) * grav_accel
    if gross_lift <= total_mass:
        raise Exception('Altitude unreachable for this configuration')

    ascent_rate = math.sqrt(free_lift / (0.5 * balloon_cd * launch_area * air_density))
    volume_ratio = launch_volume / burst_volume
    burst_altitude = -(air_density_model) * math.log(volume_ratio)
    time_to_burst = (burst_altitude / ascent_rate) / 60.0

    if math.isnan(ascent_rate):
        raise Exception('Altitude unreachable for this configuration')

    if burst_diameter >= 10 and asent_rate < 4.8:
        logger.warn('Configuration suggests a possible floater')

    return dict(ascent_rate=ascent_rate,
                burst_altitude=burst_altitude,
                time_to_burst=time_to_burst,
                neck_lift=neck_lift,
                launch_volume=launch_volume,
                burst_diameter=burst_diameter)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-tba', '--target-burst-alt', type=float, default=33000,
                        help='Target Burst Altitude in meters')
    parser.add_argument('-tar', '--target-ascent-rate', type=float, default=0,
                        help='Target Ascent Rate in meters / sec')
    parser.add_argument('-mp', '--payload-mass', type=float, default=0,
                        help='Payload Mass in grams')
    parser.add_argument('-mb', '--balloon-mass', type=float, default=0,
                        help='Balloon Mass in grams')
    parser.add_argument('-bd', '--burst-diameter', type=float, default=0,
                        help='Burst Diameter in meters')
    parser.add_argument('-cd', '--balloon-cd', type=float, default=0,
                        help='Balloon Drag Coefficient')
    parser.add_argument('-rho-d', '--gas-density', type=float, default=0.1786,
                        help='Gas Density in kg / m^3')
    parser.add_argument('-rho-a', '--air-density', type=float, default=1.2050,
                        help='Air Density in kg / m^3')
    parser.add_argument('-adm', '--air-density-model', type=float, default=7238.3,
                        help='Air Density Model')
    parser.add_argument('-ga', '--grav-accel', type=float, default=9.80665,
                        help='Gravitational Acceleration in m/s^2')

    parser.add_argument('--balloon', type=str, default=None,
                        help='Prefill balloon mass, burst diameter, and cd from ' \
                             'a preset balloon type. Use --list-balloons to see ' \
                             'all presets')

    parser.add_argument('--gas', type=str, default='he',
                        help='Type of gas used in balloon (he, h, ch4)')

    parser.add_argument('--json', action='store_true', default=False,
                        help='Format output in JSON')

    parser.add_argument('--list-balloons', action='store_true', default=False,
                        help='List all balloon types')

    args = parser.parse_args()

    if args.list_balloons:
        keys = balloons.keys()
        def balloon_sort(a, b):
            prefix_cmp = cmp(a[:1], b[:1])
            if prefix_cmp != 0:
                return prefix_cmp
            return cmp(int(a[1:]), int(b[1:]))

        keys.sort(balloon_sort)
        for key in keys:
            print '%s: %s %dg' % (key, balloons[key].manufacturer, balloons[key].mass)
        return

    if args.balloon:
        b = balloons.get(args.balloon)
        if not b:
            parser.error('Unknown ballon "%s"' % args.balloon)

        if args.balloon_mass == 0:
            args.balloon_mass = b.mass
        if args.balloon_cd == 0:
            args.balloon_cd = b.cd
        if args.burst_diameter == 0:
            args.burst_diameter = b.burst_diameter

    if args.payload_mass == 0 or args.balloon_mass == 0:
        parser.error('Payload mass and balloon mass are required')

    try:
        burst = calc_burst(target_burst_alt=args.target_burst_alt,
                           target_ascent_rate=args.target_ascent_rate,
                           payload_mass=args.payload_mass,
                           balloon_mass=args.balloon_mass,
                           burst_diameter=args.burst_diameter,
                           balloon_cd=args.balloon_cd,
                           gas_density=args.gas_density,
                           air_density=args.air_density,
                           air_density_model=args.air_density_model,
                           grav_accel=args.grav_accel)
    except Exception, e:
        if args.json:
            print json.dumps(dict(error=str(e)))
            return
        parser.error(e)

    if args.json:
        print json.dumps(burst, sort_keys=True, indent=4, separators=(',', ': '))
        return

    alt = burst['burst_altitude'] / 1000.0
    lv = burst['launch_volume']
    neck_lift = burst['neck_lift']
    burst_h = int(burst['time_to_burst'] / 60.0)
    burst_m = burst['time_to_burst'] % 60

    data = '''
* Payload mass: {mass:.0f} g
* Target Burst Altitude: {alt:.1f} km
* Balloon burst diameter: {burst_diameter:.1f} m
* Ascent Rate: {ascent_rate:.2f} m/s
* Time to Burst: {burst_h:.0f}h {burst_m:.0f}m
* Neck Lift: {neck_lift:.0f} g / {neck_lift_lb:.1f} lbs
* Launch Volume: {launch_volume:.2f} m^3 / {lv_L:.2f} L / {lv_ft3:.2f} ft^3'''

    print data.format(mass=args.payload_mass, alt=alt,
                      lv_L=lv * 1000, lv_ft3=lv * 35.31,
                      neck_lift_lb=neck_lift * 0.00220462,
                      burst_h=burst_h, burst_m=burst_m, **burst)

if __name__ == '__main__':
    main()
