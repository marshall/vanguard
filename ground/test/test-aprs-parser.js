import test from 'unit.js';
import { Parser } from '../lib/parsers/aprs';
import moment from 'moment';

describe('parsers/aprs', () => {
    let parser;
    beforeEach(() => { parser = new Parser() });

    it('should parse location', done => {
        let locationString = 'APRS: N5JHH-2>APRS,APRS,TCPIP*:/152712h3312.86N/09708.12WO000/000/A=000571';
        
        parser.on('data', msg => {
            let date = moment().format('MM DD YYYY ');
            let time = '15 27 12';
            let datetime = date.concat(time);
            let calculatedTimestamp = moment().utc(datetime) / 1000;
            let mapsURL = ' http://www.maps.google.com/?q=33.21433333,-97.13533333';
            
            test
                .value(msg.type).isEqualTo('location')
                .value(msg.timestamp).isApprox(calculatedTimestamp, 0.1)
                .value(msg.lat).isEqualTo(33.21433333)
                .value(msg.lon).isEqualTo(-97.13533333)
                .value(msg.course).isEqualTo(0)
                .value(msg.speed).isEqualTo(0)
                .value(msg.alt).isEqualTo(174.04079443069458)
                .value(msg.url).isEqualTo(mapsURL);
            done();
        });

        parser.write(locationString);
    });

    it('should parse telemetry', done => {
        let telemetryString = 'APRS: N5JHH-2>APRS,APRS,TCPIP*:T#804,019,000,024,383,027,00000000';
        
        parser.on('data', msg => {
            test
                .value(msg.type).isEqualTo('telemetry')
                .value(msg.packetId).isEqualTo(804)
                .value(msg.intTemp).isEqualTo(19)
                .value(msg.extTemp).isEqualTo(0)
                .value(msg.cpu).isEqualTo(24)
                .value(msg.freeMem).isEqualTo(383)
                .value(msg.uptime).isEqualTo(27)
                .value(msg.d).isEqualTo(0);
            done();
        });

        parser.write(telemetryString);
    });
});