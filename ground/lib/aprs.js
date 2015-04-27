import _ from 'lodash';
import { EventEmitter } from 'events';
import log from './log';
import net from 'net';
import printf from 'printf';
import util from 'util';
import Promise from 'promise';

export var callsign = 'N0CALL';

export function setCallsign(c) {
  callsign = c || 'N0CALL';
}

export class Client extends EventEmitter {
  constructor(options) {
    super();
    this.reset();

    _.merge(this, _.pick(options, 'name', 'version'));
    if (options && options.autoConnect) {
      this.connect(options);
    }
  }

  reset() {
    this._socket = new net.Socket();
    this._socket.setEncoding('utf8');
    this._data = '';
    this.state = 'disconnected';
    this.serverInfo = {};
    this.verified = false;
    this.name = 'vanguard-aprs-client';
    this.version = '0.0.1';
    this.host = 'noam.aprs2.net',
    this.port = 14580,
    this.user = callsign;
    this.pass = '-1';
    this.filter = '';
    this.autoLogin = true;
  }

  connect(options) {
    _.merge(this, _.pick(options, 'host', 'port', 'user', 'pass', 'filter',
                                  'autoLogin'));

    this._socket.once('connect', () => {
      this.state = 'connected';
      this._socket.on('data', data => this.parse(data))
      this.emit('connect');

      if (this.autoLogin) {
        this.login(this.user, this.pass, this.filter);
      }
    });

    this._socket.on('end', () => this.reset());
    this._socket.connect(this.port, this.host);
  }

  waitForLogin() {
    return new Promise((resolve, reject) => {
      switch (this.state) {
        case 'connected':
          this.once('server-info', () => resolve());
          break;
        case 'need-login':
          resolve();
          break;
        default:
          reject('Not connected');
          break;
      }
    });
  }

  login(user, pass, filter) {
    return this.waitForLogin().then(new Promise((resolve, reject) => {
      user = user || this.user;
      pass = pass || this.pass;
      filter = filter || this.filter;

      let line = printf('user %s pass %s vers %s %s', user, pass,
                        this.name, this.version);
      if (filter) {
        line += ' filter ' + filter;
      }

      this.once('login', () => { resolve(this.verified) });
      this.sendLine(line);
    }));
  }

  parse(data) {
    this._data += data.toString();

    let lines = this._data.split('\r\n');

    this._data = lines.pop();
    lines.forEach(line => {
      log.debug('<=', line);
      if (_.startsWith(line, '#')) {
        this.parseInfo(line);
        return;
      }

      this.emit('message', line);
    });
  }

  parseInfo(info) {
    let parts = _.compact(info.split(/[ ,#]/));
    if (parts[0] === 'logresp') {
      this.verified = parts[2] === 'verified';
      this.serverInfo.callsign = parts[4];
      this.state = 'ready';
      log.debug('emitLogin', this.verified);
      this.emit('login', this.verified);
    } else {
      this.serverInfo.softwareName = parts[0];
      this.serverInfo.softwareVersion = parts[1];
      this.state = 'need-login';
      this.emit('server-info', this.serverInfo);
    }
  }

  sendLine(line, callback) {
    log.debug('=>', line);
    this._socket.write(line + '\r\n', callback);
  }

  sendPacket(packet, callback) {
    this.sendLine(packet.toString(), callback);
  }
};

const APRSIS_PATH = 'APRS,TCPIP*';

export class Packet {
  constructor(options) {
    _.merge(this, {
      data: '',
      source: callsign
    }, options);
  }

  getData() {
    return this.data;
  }

  toString() {
    return printf('%s>%s:%s', this.source, APRSIS_PATH, this.getData());
  }
}

export class Position extends Packet {
  constructor(options) {
    super(_.defaults(options, {
      latitude: 0,
      longitude: 0,
      altitude: 0, // feet
      course: 0,
      speed: 0, // km/h
      time: new Date()
    }));
  }

  getData() {
    return printf('/%s%s/%sO%03.0f/%03.0f/A=%06.0f',
                  Position.encodeTime(this.time),
                  Position.encodeLatitude(this.latitude),
                  Position.encodeLongitude(this.longitude),
                  this.course,
                  this.speed,
                  this.altitude);
  }

  static encodeTime(date) {
    return printf('%02d%02d%02dh', date.getUTCHours(), date.getUTCMinutes(),
                  date.getUTCSeconds());
  }

  static encodeLatitude(value) {
    return Position.encodeCoordinate(value, 'latitude');
  }

  static encodeLongitude(value) {
    return Position.encodeCoordinate(value, 'longitude');
  }

  static encodeCoordinate(value, type) {
    type = type || 'latitude';
    let degrees = Math.abs(~~value);
    let minutes = Math.abs(~~value - value) * 60;
    let suffix, degreesFormat;

    if (type === 'latitude') {
      suffix = value >= 0 ? 'N' : 'S';
      degreesFormat = '%02d';
    } else {
      suffix = value >= 0 ? 'E' : 'W';
      degreesFormat = '%03d';
    }

    return [printf(degreesFormat, degrees),
            printf('%05.2f', minutes),
            suffix].join('');
  }
}
