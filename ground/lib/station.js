import BufferOffset from 'buffer-offset';
import _ from 'lodash';
import { EventEmitter } from 'events';
import fs from 'fs';
import mkdirp from 'mkdirp';
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
import * as vanguard from './parsers/vanguard';
import { Parser as NmeaParser } from './parsers/nmea';
import * as repl from './repl';
import TrackDB from './trackdb';
import * as aprs from './aprs';

const APRS_INTERVAL = 30000; // Every 30 seconds

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
      remoteURL: options.remoteUrl,
    });

    this.aprsClient = new aprs.Client({
      // TODO: make these configurable
      user: 'N5JHH-2',
      pass: '16287'
    });
    this.aprsLast = null;

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

    if (msg.type === 'location') {
      this.aprsPublish(msg);
    }
    if (msg.type === 'program-result'){
      this.handleResult(msg);
    }
  }

  aprsPublish(location) {
    if (this.aprsClient.state !== 'ready') {
      return;
    }

    let now = new Date();
    if (this.aprsLast === null ||
        now - this.aprsLast >= APRS_INTERVAL) {

      this.aprsClient.sendPacket(new aprs.Position({
        latitude: location.lat,
        longitude: location.lon,
        altitude: (location.alt / 1000.0) * 3.28084
      }));

      this.aprsLast = new Date();
    }
  }

  handleResult(msg){
    let programDir = path.join('/tmp', 'vanguard', 'uploads', 'results', msg.programName);
    let chunkName = 'chunk' + msg.chunk + '.dat';
    let chunkPath = path.join(programDir, chunkName);
    let indexFile = path.join(programDir, 'index.kbf');
    log.debug('Received chunk %d of %d for program %s', msg.chunk, msg.chunkCount, msg.programName);

    if(!fs.existsSync(programDir)){ // first result msg for program
      mkdirp.sync(programDir);
      fs.writeFileSync(chunkPath, msg.programData);
      let size = 2 + msg.chunkCount;
      let buf = new BufferOffset(size);
      buf.appendInt8(msg.chunkCount);
      let boolArr =[];
      for(let x = 0; x < msg.chunkCount; x++){
        boolArr.push(false);
      }
      boolArr[msg.index] = true;
      buf.append(new Buffer(boolArr));
      fs.writeFileSync(indexFile, buf); 

      if(msg.chunkCount === 1){
        this.assembleFile(msg);
      }
    } else { // partially received program
      fs.writeFileSync(chunkPath, msg.programData);
      let resultBuffer = new BufferOffset(fs.readFileSync(indexFile));
      let readSize = resultBuffer.getInt8();
      let tempVal = 0;
      let resultArr = [];
      for (let y = 0; y < readSize; y++){
        tempVal = resultBuffer.getInt8();
        if(tempVal === 1){
          resultArr.push(true);
        } else {
          resultArr.push(false);
        }
      } 
      resultArr[msg.index] = true;
      let size = 2 + msg.chunkCount;
      let updatedBuffer = new BufferOffset(size);
      updatedBuffer.appendInt8(msg.chunkCount);
      updatedBuffer.append(new Buffer(resultArr));
      fs.writeFileSync(indexFile, updatedBuffer); 
      if(resultArr.every(elem => elem == true) ){
        this.assembleFile(msg);
      }
    }
  }

  assembleFile(msg){
    let fileString = '', chunkPath = '', chunkFileName = '';
    let programDir = path.join('/tmp', 'vanguard', 'uploads', 'results', msg.programName);
    let stdoutFile = path.join(programDir, 'stdout.log');
    for(let x = 1; x <= msg.chunkCount; x++){
      chunkFileName = 'chunk' + x + '.dat';
      chunkPath = path.join(programDir, chunkFileName)
      fileString = fs.readFileSync(chunkPath);
      fs.appendFileSync(stdoutFile, fileString);
    }
    log.debug("Successfully assembled stdout.log for program %s", msg.programName);
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

  upload(filePath) {
    return new Promise((resolve, reject) => { 
      if (!this.radioOut){
        reject('Radio output not Connected');
        return;
      }

      let programName = path.basename(filePath, '.js');
      let programNameLength = programName.length;
      let maxDataLength = 255 - vanguard.ENVELOPE_SIZE - vanguard.PROGRAM_UPLOAD_HEADER_SIZE - programNameLength;
      let stats = fs.statSync(filePath);
      let size = stats['size'];
      let numChunks = Math.ceil(size/maxDataLength);
      let programDataStr = fs.readFileSync(filePath, "utf8");
      let stagingDir = path.join(path.dirname(path.dirname(__dirname)), 'uploads', 'sendStaging', programName);
      
      if (!fs.existsSync(stagingDir)){
        mkdirp.sync(stagingDir);
      }
      let offset = 0;
      fs.open(filePath, 'r', function(err, fd){
        for(let x = 0; x < numChunks; x++){
           if(size < maxDataLength){
              maxDataLength = size; //prevent reading more bytes than the file
            }
            let chunkName = 'chunk' + x + '.dat';
            let buf = new Buffer(maxDataLength);
            fs.readSync(fd, buf, 0, maxDataLength, offset); 
            fs.writeFileSync(stagingDir + chunkName, buf);
            offset += maxDataLength;
            size -= maxDataLength;
        }
      });
      log.debug('Split file %s into %d chunks..', programName, numChunks);
      
      let self = this;
      this.on('message', function handler(msg){
        if(msg.type === 'program-result'){    
          self.removeListener('message', handler);
          resolve(msg);
        }
      });

      for(let x = 0; x < numChunks; x++){
        let chunkName = 'chunk' + x + '.dat'
        let chunkPath = path.join(stagingDir, chunkName);
        let chunkDataStr = fs.readFileSync(chunkPath);
        let programData = {index:x, chunk:x+1, chunkCount:numChunks, programNameLen:programName.length, programDataLen:chunkDataStr.length, programName:programName, programData:chunkDataStr};
        this.radioOut.write(new Buffer(Message.fromProgramUpload(programData)));
      }
    });
  }
};
