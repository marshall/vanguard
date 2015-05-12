import { install } from 'source-map-support';
install();

import _ from 'lodash';
import BufferOffset from 'buffer-offset';
import bunyan from 'bunyan';
import nlj from 'newline-json';
import program from 'commander';

import * as vanguard from '../lib/parsers/vanguard';
import MockData from './mock-data';

class VgFormatter {
  format(data) {
    switch (data.type) {
      case 'location':
        return new Buffer(vanguard.Message.fromLocation(data));
      case 'telemetry':
        return new Buffer(vanguard.Message.fromTelemetry(data));
      case 'photo-data':
        return new Buffer(vanguard.Message.fromPhotoData(data));
      case 'pong':
        return new Buffer(vanguard.Message.fromPong(data));
    }
  }
}

class VgBase64Formatter extends VgFormatter {
  format(data) {
    return super.format(data).toString('base64') + '\n';
  }
}

class JsonFormatter {
  format(data) {
    switch (data.type) {
      case 'photo-data':
        // this falls through on purpose
        data.data = data.data.toString('base64');
      default:
        return JSON.stringify(data) + '\n';
    }
  }
}

const FORMATTERS = {
  vanguard: new VgFormatter(),
  'vanguard-base64': new VgBase64Formatter(),
  json: new JsonFormatter()
};

const LOCATION_INTERVAL  = 1000;
const TELEMETRY_INTERVAL = 2000;
const PHOTO_DOWNLOAD_INTERVAL = 3000;

class MockBalloon {
  constructor() {
    program
      .version('0.0.1')
      .option('-o, --output <format>',
              'Output format: one of vanguard, vanguard-base64, json [vanguard]',
              'vanguard')
      .parse(process.argv);

    this.mockData = new MockData();
    this.timers = [];
    this.formatter = FORMATTERS[program.output] || FORMATTERS.vanguard;

    let parser = new vanguard.Parser();
    parser.on('data', data => this.handleMessage(data));
    process.stdin.pipe(parser);
  }

  start() {
    this.timers.push(setInterval(() => this.mockData.nextData(), 1000));
    this.timers.push(setInterval(() => this.nextLocation(), LOCATION_INTERVAL));
    this.timers.push(setInterval(() => this.nextTelemetry(), TELEMETRY_INTERVAL));
    this.timers.push(setInterval(() => this.nextPhotoData(), PHOTO_DOWNLOAD_INTERVAL));
  }

  stop() {
    this.timers.forEach(timer => {
      clearInterval(timer);
    });
  }

  dumpData(data) {
    process.stdout.write(this.formatter.format(data));
  }

  nextLocation() {
    this.dumpData({
      type: 'location',
      lat: this.mockData.location.latitude,
      lon: this.mockData.location.longitude,
      alt: this.mockData.location.altitude,
      quality: this.mockData.location.quality,
      satellites: this.mockData.location.satellites,
      speed: this.mockData.location.speed
    });
  }

  nextTelemetry() {
    this.dumpData({
      type: 'telemetry',
      uptime: this.mockData.uptime,
      mode: this.mockData.mode,
      cpu: this.mockData.cpu,
      freeMem: this.mockData.freeMem,
      intTemp: this.mockData.intTemp,
      intHumidity: this.mockData.intHumidity,
      extTemp: this.mockData.extTemp
    });
  }

  nextPhotoData() {
    this.mockData.nextPhotoData();
    this.dumpData(_.merge(this.mockData.mockPhotoData, {
      type: 'photo-data'
    }));
  }

  handleMessage(msg) {
    switch (msg.type) {
      case 'ping':
        msg.type = 'pong';
        this.dumpData(msg);
        break;
    }
  }
}

new MockBalloon().start();
