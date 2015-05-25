import _ from 'lodash';
import { EventEmitter } from 'events';
import fs from 'fs';
import net from 'net';
import nlj from 'newline-json';
import nmea from 'nmea';
import os from 'os';
import path from 'path';
import Promise from 'promise';
import serialport, { SerialPort } from 'serialport';
import { spawn, fork } from 'child_process';
import util from 'util';
import uuid from 'uuid';

import log from './log';
import { Parser as VgParser, Message } from './parsers/vanguard';
import { Parser as NmeaParser } from './parsers/nmea';
import * as repl from './repl';
import TrackDB from './trackdb';

export class Station extends EventEmitter {
  constructor(options) {
    super();

    this.lastMsg = {__all__: null};

    options = _.defaults(options || {}, {
      mock: false,
      radio: null,
      radioBaud: 9600,
      gps: null,
      gpsBaud: 9600,
      remoteUrl: null,
      serverPort: 41001,
      replPort: 41002
    });

    this.mock = options.mock;
    this.radioDevice = options.radio;
    this.radioBaud = parseInt(options.radioBaud);
    this.gpsDevice = options.gps;
    this.gpsBaud = parseInt(options.gpsBaud);
    this.serverPort = parseInt(options.serverPort);
    this.replPort = parseInt(options.replPort);

    this.trackDB = new TrackDB(this, {
      remoteURL: options.remoteUrl
    });

    this.startServers();
    log.info('Ground station listening');
  }

  startServers() {
    this.connections = [];
    var self = this;
    this.server = net.createServer(function(conn) {
      conn.on('close', () => _.remove(self.connections, conn));
      self.connections.push(conn);
    });
    this.server.listen(this.serverPort);
    this.replServer = repl.listen(this, this.replPort);
  }

  onExit() {
    this.connections.forEach(conn => {
      conn.end();
    });

    if (this.server) {
      this.server.close();
    }

    if (this.replServer) {
      this.replServer.close();
    }
  }

  checkRadio() {
    return new Promise((resolve, reject) => {
      if (this.radioDevice || this.mock) {
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
        this.radioIn = process.stdin;
        this.radioOut = null;
        process.stdin.once('readable', resolve);
        return;
      }

      if (this.mock) {
        let proc = spawn(process.execPath,
                         [__dirname + '/../mock/mock-balloon.js']);
        this.radioIn = proc.stdout;
        this.radioOut = proc.stdin;
        resolve();
        return;
      }

      log.info('Serial device: %s, baudrate: %d', this.radioDevice, this.radioBaud);
      var port = new SerialPort(this.radioDevice, {
        baudrate: this.radioBaud
      });
      this.radioOut = this.radioIn = port;
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
          this.startParser(this.radioIn, 'radio', VgParser);
        })
        .catch(err => {
          log.error(err);
          process.exit(1);
        });
  }

  startParser(stream, source, Parser) {
    var parser = new Parser();
    parser.on('data', data => {
      this.handleMessage(source, data);
    });

    stream.pipe(parser);
  }

  handleMessage(source, msg) {
    this.lastMsg.__all__ = msg;
    this.lastMsg[msg.type] = msg;

    msg.source = source;
    log.debug(msg, 'received');

    this.emit('message', msg);
    this._broadcast(msg);
  }

  _broadcast(msg) {
    this.connections.forEach(conn => {
      conn.write(JSON.stringify(msg) + '\n');
    });
  }

  getLastMessage(type) {
    return this.lastMsg[type || '__all__'];
  }

  ping(magic) {
    return new Promise((resolve, reject) => {
      if (!this.radioOut) {
        reject('Radio output not connected');
        return;
      }

      var self = this;
      this.on('message', function handler(msg) {
        if (msg.type === 'pong' && msg.magic === magic) {
          self.removeListener('message', handler);
          resolve(msg);
        }
      });

      this.radioOut.write(new Buffer(Message.fromPing({ magic })));
    });
  }

  upload(path) {
  }
};
