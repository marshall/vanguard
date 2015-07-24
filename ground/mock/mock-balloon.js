import { install } from 'source-map-support';
install();

import _ from 'lodash';
import BufferOffset from 'buffer-offset';
import bunyan from 'bunyan';
import mkdirp from 'mkdirp';
import nlj from 'newline-json';
import program from 'commander';

import * as vanguard from '../lib/parsers/vanguard';
import MockData from './mock-data';
import fs from 'fs';
import path from 'path';
import child_process from 'child_process'

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
      case 'program-result':
        return new Buffer(vanguard.Message.fromProgramResult(data));
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
      case 'program-upload':
        this.handleUpload(msg);
        break;
    }
  }

  handleUpload(msg){
    let exitCode = -127;
    let stagingDir = path.join('/tmp', 'vanguard', 'mockBalloon', 'uploads', msg.programName);

    let sendStagingDir = path.join(stagingDir, 'send');
    var self = this;
    if (!fs.existsSync(sendStagingDir)){
      mkdirp.sync(sendStagingDir);
    } 
    let chunkName = 'chunk' + msg.chunk + '.dat';
    let mainFilePath = path.join(stagingDir, 'main.js');
    let outputFilePath = path.join(stagingDir , 'stdout.log');
    let errFilePath = path.join(stagingDir, 'stderr.log');
    let mylog = path.join(stagingDir, 'mylog.log');
    fs.writeFileSync(path.join(stagingDir, chunkName), msg.programData);
    if(msg.chunk === msg.chunkCount){  //because it's the mock balloon messages are always received in order
      let fileString = '';
      let chunkName = '';
      for(let z = 1; z <= msg.chunkCount; z++){ //assemble main.js
        chunkName = 'chunk' + z + '.dat';
        fileString = fs.readFileSync(path.join(stagingDir, chunkName));
        fs.appendFileSync(mainFilePath, fileString);
      }

      let ls = child_process.spawn('node', [mainFilePath]);
      ls.stdout.on('data',function(data){
        fs.appendFileSync(outputFilePath, data);
      });

      ls.stderr.on('data',function(data){
        fs.appendFileSync(errFilePath, data);
      });

      ls.on('exit', function (code) {
        exitCode = code;
        let maxDataLength = 255 - vanguard.ENVELOPE_SIZE - vanguard.PROGRAM_RESULT_HEADER_SIZE - msg.programNameLen;
        let stats = fs.statSync(outputFilePath);
        let remainingSize = stats['size'];
        let numChunks = Math.ceil(remainingSize/maxDataLength);
        let offset = 0;
        msg.exitCode = code;
        msg.type = 'program-result';
        msg.chunkCount = numChunks;
        fs.open(outputFilePath, 'r', function(err, fd){
          for(let x = 1; x <= numChunks; x++){
             if(remainingSize < maxDataLength){
                maxDataLength = remainingSize;
              }
              let chunkName = 'chunk' + x + '.dat';
              let chunkPath = path.join(sendStagingDir, chunkName);
              let buf = new Buffer(maxDataLength);
              fs.readSync(fd, buf, 0, maxDataLength, offset);
              offset += maxDataLength;
              remainingSize -= maxDataLength;
              fs.writeFileSync(chunkPath, buf);
              msg.chunk = x;
              msg.index = x-1;
              msg.programData = buf;
              msg.programDataLen = buf.length;
              self.dumpData(msg);
              if(msg.chunk == 1){
                self.dumpData(msg);
              }
          }
        });
      });

    }
  }
}

new MockBalloon().start();
