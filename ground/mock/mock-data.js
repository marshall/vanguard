import _ from 'lodash';
import fs from 'fs';
import path from 'path';

const FLIGHT_MODES = ['preflight', 'ascent', 'descent', 'landed'];
const CHUNK_SIZE = 200;

class MockPhoto {
  constructor(path) {
    this.setPhoto(path);
  }

  setPhoto(path) {
    this.txChunk = -1;
    this.buffer = fs.readFileSync(path);
    this.fileSize = this.buffer.length;
    this.chunkCount = (this.buffer.length / CHUNK_SIZE).toFixed();

    if (this.buffer.length % CHUNK_SIZE > 0) {
      this.chunkCount++;
    }
    this.genTxOrder();
  }

  genTxOrder() {
    this.txOrder = _.shuffle(_.range(this.chunkCount));
  }

  getChunk(i) {
    let chunkSize = CHUNK_SIZE;
    if (i === this.chunkCount - 1) {
      let leftOver = this.buffer.length % CHUNK_SIZE;
      if (leftOver > 0) {
        chunkSize = leftOver;
      }
    }

    let offset = i * CHUNK_SIZE;
    return this.buffer.slice(offset, offset + chunkSize);
  }

  nextChunk() {
    if (this.txOrder.length === 0) {
      this.genTxOrder();
    }

    this.txChunk = this.txOrder.pop();
    return {
      chunk: this.txChunk,
      data: this.getChunk(this.txChunk)
    };
  }
}

export default class MockData {
  constructor() {
    this.uptime = 0;
    this.downloading = false;
    this.mockPhoto = new MockPhoto(path.join(__dirname, 'photo.jpg'));
  }

  randFloat(min, max) {
    return Math.random() * (max - min) + min;
  }

  randInt(min, max) {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  randLat() {
    return this.randFloat(33, 34);
  }

  randLong() {
    return this.randFloat(-98, -97);
  }

  nextData() {
    this.uptime++;
    this.cpu = this.randInt(0, 100);
    this.intTemp = this.randInt(-40, 100);
    this.intHumidity = this.randInt(0, 100);
    this.extTemp = this.randInt(-40, 100);
    this.freeMem = this.randInt(0, 512);
    this.mode = FLIGHT_MODES[this.randInt(0, FLIGHT_MODES.length - 1)];

    this.location = {
      latitude: this.randLat(),
      longitude: this.randLong(),
      altitude: this.randFloat(0, 50),
      quality: this.randInt(0, 2),
      satellites: this.randInt(0, 5),
      speed: this.randFloat(0, 100),
      timestamp: [ this.randInt(0, 23),
      this.randInt(0, 59),
      this.randInt(0, 59) ],
    };
  }

  nextPhotoData() {
    let chunk = this.mockPhoto.nextChunk();
    this.mockPhotoData = {
      index: 0,
      chunk: chunk.chunk,
      chunkCount: this.mockPhoto.chunkCount,
      fileSize: this.mockPhoto.fileSize,
      data: chunk.data
    };
  }
}
