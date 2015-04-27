import _ from 'lodash';
import { EventEmitter } from 'events';
import fs from 'fs';
import log from './log';
import nmea from 'nmea';
import os from 'os';
import path from 'path';
import Promise from 'promise';
import serialport, { SerialPort } from 'serialport';
import TrackDB from './trackdb';
import util from 'util';
import uuid from 'uuid';

import { Parser as VgParser } from './parsers/vanguard';
import { Parser as NmeaParser } from './parsers/nmea';

export class Station extends EventEmitter {
  constructor(options) {
    super();

    log.info('station ctor');
    if (!options) options = {};

    this.radioDevice = options.radio;
    this.readStdin = this.radioDevice === '-';
    this.radioBaud = parseInt(options.radioBaud);
    this.gpsDevice = options.gps;
    this.gpsBaud = parseInt(options.gpsBaud);

    this.trackDB = new TrackDB(this, {
      remoteURL: options.remoteUrl
    });
  }

  checkRadio() {
    log.info('check radio');
    return new Promise((resolve, reject) => {
      if (this.radioDevice) {
        log.info('should resolve');
        resolve(this.radioDevice);
        return;
      }
      this.detectRadio(resolve, reject);
    });
  }

  detectRadio(resolve, reject) {
    log.warn('No radio device supplied, attempting to detect');

    serialport.list((err, ports) => {
      if (err) {
        reject(err);
        return;
      }

      if (os.type() === 'Darwin') {
        _.remove(ports, port => {
          return port.comName === '/dev/cu.Bluetooth-Modem' ||
                 port.comName === '/dev/cu.Bluetooth-Incoming-Port';
        });
      }

      if (ports.length === 0) {
        reject('No detected serial ports');
        return;
      }

      ports = _.pluck(ports, 'comName');

      if (ports.length > 1) {
        log.warn('Multiple serial ports found, choosing first');
      }

      log.info('Detected serial port: %s', ports[0]);
      resolve(ports[0]);
    });
  }

  openRadio() {
    return new Promise((resolve, reject) => {
      if (this.radioDevice === '-') {
        this.radioStream = process.stdin;
        process.stdin.on('readable', resolve);
        return;
      }

      log.info('Serial device: %s, baudrate: %d', this.radioDevice, this.radioBaud);
      var port = new SerialPort(this.radioDevice, {
        baudrate: this.radioBaud
      });
      this.radioStream = port;
      port.on('open', resolve);
    });
  }

  openGPS() {
    return new Promise((resolve, reject) => {
      if (!this.gpsDevice) {
        reject('No GPS device, ground station locations will not be sent');
        return;
      }

      var port = new SerialPort(this.gpsDevice, {
        baudrate: this.gpsBaud
      });

      this.gpsStream = port;
      port.on('open', resolve);
    });
  }

  start() {
    this.checkRadio()
        .then(this.openRadio())
        .then(() => {
          this.startParser(this.radioStream, 'radio', VgParser);
        })
        .catch(err => {
          log.error(err);
          process.exit(1);
        });

    /*this.openGPS()
        .then(() => {
          this.startParser(this.gpsStream, 'gps', NmeaParser);
        })
        .catch(err => {
          // GPS isn't required for ground station operations
          log.warn(err);
        });*/
  }

  startParser(stream, source, Parser) {
    log.info('start parser');
    var parser = new Parser();
    parser.on('data', data => {
      log.info('got data', data);
      this.handleMessage(source, data);
    });

    stream.pipe(parser);
  }

  handleMessage(source, msg) {
    msg.source = source;
    log.debug(util.format('[%s]<-%s: %j', source, msg.type, msg));

    this.emit('message', msg);
  }
};
