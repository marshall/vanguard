import test from 'unit.js';
import { Parser } from '../lib/parsers/nmea';
import nmea from 'nmea';
import Promise from 'promise';
import { Readable } from 'stream';

describe('parsers/nmea', () => {
  function buildParser(options) {
    let parser = new Parser(options);
    parser.parse = function(data) {
      return new Promise((resolve, reject) => {
        let results = { data: [], invalid: [] };
        this.on('data', obj => { results.data.push(obj) });
        this.on('invalid', err => { results.invalid.push(err) });
        this.on('end', () => { resolve(results) });
        this.write(data);
        this.end();
      });
    };
    return parser;
  }

  it('should parse GGA sentence', () => {
    let sentence =
      "$IIGGA,123519,4807.04,N,1131.00,E,1,8,0.9,545.9,M,46.9,M,,*52\r\n";
    let parser = buildParser();

    return test.promise
      .given(parser.parse(sentence))
      .then(results => {
        let data = results.data;
        let fix;
        test
          .value(data.length).isEqualTo(1)
          .given(fix = data[0])
            .value(fix.lat.toFixed(4)).isEqualTo(48.1173)
            .value(fix.lon.toFixed(4)).isEqualTo(11.5167)
            .value(fix.alt).isEqualTo(545.9)
            .value(fix.timestamp).isEqualTo(123519)
            .value(fix.satellites).isEqualTo(8);
      })
      .catch(err => test.fail(err.message));
  });

  it('emits invalid on invalid sentence', () => {
    let parser = buildParser();
    return test.promise
      .given(parser.parse('&&&&&'))
      .then(results => {
        test.value(results.invalid.length).isEqualTo(1);
      })
      .catch(err => test.fail(err.message));
  });

  it('drops invalid sentences', () => {
    let sentences = [
      "$IIGGA,123519,4807.04,N,1131.00,E,1,8,0.9,545.9,M,46.9,M,,*52\r\n",
      "$IIGGA,123519,4807.04,N,1131.00,E,1,8,0.9,545.9,M,46.9,M,,*00\r\n", // invalid checksum
      "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47\r\n"
    ];
    let parser = buildParser({ dropInvalid: true });

    return test.promise
      .given(parser.parse(sentences.join('')))
      .then(results => {
        let data = results.data;
        test.value(data.length).isEqualTo(2);
      })
      .catch(err => test.fail(err.message));
  });
});
