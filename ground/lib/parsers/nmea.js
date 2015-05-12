import nmea from 'nmea';
import nmeaHelpers from 'nmea/helpers';
import serialport from 'serialport';
import { StringDecoder } from 'string_decoder';
import { Transform } from 'stream';
import util from 'util';

export class Parser extends Transform {
  constructor(options) {
    super({ objectMode: true });
    this._buffer = '';
    this._decoder = new StringDecoder('utf8');
    this._dropInvalid = options ? options.dropInvalid : false;
  }

  _transform(chunk, encoding, done) {
    this._buffer += this._decoder.write(chunk);
    // split on newlines
    let lines = this._buffer.split(/\r?\n/);
    // keep the last partial line buffered
    this._buffer = lines.pop();
    for (let l = 0; l < lines.length; l++) {
      let line = lines[l];
      let obj;
      try {
        obj = nmea.parse(line);

        // push the parsed object out to the readable consumer
        this.push(obj);
      } catch (er) {
        this.emit('invalid', er);
        if (!this._dropInvalid) {
          done();
          return;
        }
      }
    }
    done();
  }

  _flush(done) {
    // Just handle any leftover
    let rem = this._buffer.trim();
    if (rem) {
      try {
        let obj = nmea.parse(rem);
        // push the parsed object out to the readable consumer
        this.push(obj);
      } catch (er) {
        this.emit('invalid', er);
        done();
        return;
      }
    }
    done();
  }

  push(data) {
    if (!data) {
      super.push(null);
      return;
    }

    let normalized = data;
    switch (data.type) {
      case 'fix':
        normalized = {
          lat: parseFloat(nmeaHelpers.parseLatitude(data.lat, data.latPole)),
          lon: parseFloat(nmeaHelpers.parseLongitude(data.lon, data.lonPole)),
          alt: parseFloat(nmeaHelpers.parseAltitude(data.alt, data.altUnit)),
          timestamp: data.timestamp,
          satellites: data.numSat
        };
        break;
    }
    super.push(normalized);
  }
};
