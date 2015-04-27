import _ from 'lodash';
import assert from 'assert';
import BufferOffset from 'buffer-offset';
import Dissolve from 'dissolve';
import { Location, PhotoData, Telemetry } from '../messages';
import Struct from 'struct';
import { Transform } from 'stream';
import util from 'util';

/**
 * Vanguard binary protocol: Network byte order (big endian)
 *
 *                    ord('V') + ord('M')  ord('S') + ord('G')
 * bytes 0  .. 1     : 0xa39a (begin msg - uint16_t)
 * bytes 2  .. 5     : timestamp (uint32_t - seconds since epoch)
 * byte  6           : Message type (uint8_t)
 * byte  7           : Length of data segment (uint8_t)
 * bytes 8  .. 11    : CRC32 of data (uint32_t)
 * bytes 12 .. N     : Message data
 *
 *                    ord('V') + ord('E')  ord('N') + ord('D')
 * bytes N+1 .. N+2 : 0x9b92 (end msg - uint16_t)
*/

export const BEGIN          = 0xa39a;
export const END            = 0x9b92;
export const MARKER_SIZE    = 2;
export const TIMESTAMP_SIZE = 4;
export const MSG_TYPE_SIZE  = 1;
export const LENGTH_SIZE    = 1;
export const CRC32_SIZE     = 4;
export const HEADER_SIZE    = MARKER_SIZE + TIMESTAMP_SIZE + MSG_TYPE_SIZE +
                              LENGTH_SIZE + CRC32_SIZE;
export const DATA_BEGIN     = HEADER_SIZE;
export const ENVELOPE_SIZE  = HEADER_SIZE + MARKER_SIZE;

export const MSG_TYPE_UNKNOWN          = -1;
export const MSG_TYPE_LOCATION         = 0;
export const MSG_TYPE_TELEMETRY        = 1;
export const MSG_TYPE_PHOTO_DATA       = 3;
export const MSG_TYPE_START_PHOTO_DATA = 10;
export const MSG_TYPE_STOP_PHOTO_DATA  = 11;

export const LOCATION_SIZE          = 26;
export const TELEMETRY_SIZE         = 20;
export const PHOTO_DATA_HEADER_SIZE = 10;

let Header = Struct().word16Ube('begin')
                     .word32Ube('timestamp')
                     .word8('type')
                     .word8('dataLength')
                     .word32Ube('crc32');

export class Parser extends Dissolve {
  constructor() {
    super();
    this.loop(end => {
      this.parse();
    });
  }

  parse() {
    this.uint16be('begin').tap(() => {
      if (this.vars.begin !== BEGIN) {
        return;
      }
      this.parseTimestamp();
    });
  }

  parseTimestamp() {
    this.uint32be('timestamp').tap(() => {
      this.parseMessage();
    });
  }

  parseMessage() {
    this.uint8('type').uint8('size').uint32be('crc32').tap(() => {
      this.tapMessage();
    });
  }

  tapMessage() {
    switch (this.vars.type) {
      case MSG_TYPE_LOCATION:
          assert.equal(this.vars.size, LOCATION_SIZE);
          this.doublebe('lat')
              .doublebe('lon')
              .floatbe('alt')
              .uint8('quality')
              .uint8('satellites')
              .floatbe('speed')
              .pushMessage();
          break;

      case MSG_TYPE_TELEMETRY:
          assert.equal(this.vars.size, TELEMETRY_SIZE);
          this.uint32be('uptime')
              .uint8('mode')
              .uint8('cpu')
              .uint16be('freeMem')
              .floatbe('intTemp')
              .floatbe('intHumidity')
              .floatbe('extTemp')
              .pushMessage();
          break;

      case MSG_TYPE_PHOTO_DATA:
          this.uint16be('index')
              .uint16be('chunk')
              .uint16be('chunkCount')
              .uint32be('fileSize')
              .buffer('data', this.vars.size - 10)
              .pushMessage();
          break;
    }
  }

  pushMessage() {
    this.tap(() => {
      this.push(this.vars);
      this.vars = {};
    });
  }

  push(msg) {
    if (!msg) {
      return super.push(msg);
    }

    let type = msg.type;
    let data = _.omit(msg, 'begin', 'timestamp', 'type', 'size', 'crc32');
    switch (type) {
      case MSG_TYPE_LOCATION:
        super.push(new Location(data));
        break;
      case MSG_TYPE_TELEMETRY:
        super.push(new Telemetry(data));
        break;
      case MSG_TYPE_PHOTO_DATA:
        super.push(new PhotoData(data));
        break;
    }
  }
}

export class Message extends Buffer {
  constructor(dataLength, options) {
    super(dataLength + ENVELOPE_SIZE);

    options = _.defaults(options, {
      type: MSG_TYPE_UNKNOWN,
      crc32: 0,
      timestamp: Math.floor(Date.now() / 1000)
    });

    Header._setBuff(this);
    Header.set('begin', BEGIN);
    Header.set('type', options.type);
    Header.set('crc32', options.crc32);
    Header.set('dataLength', dataLength);

    this.setTimestamp(options.timestamp);
    this.writeUInt16BE(END, DATA_BEGIN + this.getDataLength());
  }

  getTimestamp() {
    Header._setBuff(this);
    return Header.fields.timestamp;
  }

  setTimestamp(value) {
    Header._setBuff(this);
    Header.fields.timestamp = value;
  }

  getData() {
    return this.slice(DATA_BEGIN, DATA_BEGIN + this.getDataLength());
  }

  setData(value) {
    value.copy(this, DATA_BEGIN, 0, this.getDataLength());
  }

  getDataLength() {
    Header._setBuff(this);
    return Header.fields.dataLength;
  }

  static fromLocation(location) {
    let msg = new Message(LOCATION_SIZE, { type: MSG_TYPE_LOCATION });
    let data = new BufferOffset(LOCATION_SIZE);
    data.appendDoubleBE(location.lat);
    data.appendDoubleBE(location.lon);
    data.appendFloatBE(location.alt);
    data.appendUInt8(location.quality);
    data.appendUInt8(location.satellites);
    data.appendFloatBE(location.speed);
    msg.setData(data);
    return msg;
  }

  static fromTelemetry(telemetry) {
    let msg = new Message(TELEMETRY_SIZE, { type: MSG_TYPE_TELEMETRY });
    let data = new BufferOffset(TELEMETRY_SIZE);
    data.appendUInt32BE(telemetry.uptime);
    data.appendUInt8(0);
    data.appendUInt8(telemetry.cpu);
    data.appendUInt16BE(telemetry.freeMem);
    data.appendFloatBE(telemetry.intTemp);
    data.appendFloatBE(telemetry.intHumidity);
    data.appendFloatBE(telemetry.extTemp);
    msg.setData(data);
    return msg;
  }

  static fromPhotoData(photoData) {
    let dataLength = PHOTO_DATA_HEADER_SIZE + photoData.data.length;
    let msg = new Message(dataLength, { type: MSG_TYPE_PHOTO_DATA });
    let data = new BufferOffset(dataLength);
    data.appendUInt16BE(photoData.index);
    data.appendUInt16BE(photoData.chunk);
    data.appendUInt16BE(photoData.chunkCount);
    data.appendUInt32BE(photoData.fileSize);
    data.append(photoData.data);
    msg.setData(data);
    return msg;
  }
}
