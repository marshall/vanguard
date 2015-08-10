import test from 'unit.js';
import * as vanguard from '../lib/parsers/vanguard';
import BufferOffset from 'buffer-offset';

describe('parsers/vanguard', () => {
  let parser;
  beforeEach(() => { parser = new vanguard.Parser() })

  it('should parse location', done => {
    let buf = new vanguard.Message(vanguard.LOCATION_SIZE, {
      type: vanguard.MSG_TYPE_LOCATION
    });

    let data = new BufferOffset(vanguard.LOCATION_SIZE);
    data.appendDoubleBE(1.1);
    data.appendDoubleBE(2.2);
    data.appendFloatBE(3.3);
    data.appendUInt8(100);
    data.appendUInt8(5);
    data.appendFloatBE(2);
    buf.setData(data);

    parser.on('data', msg => {
      test
        .value(msg.lat.toFixed(1)).isEqualTo(1.1)
        .value(msg.lon.toFixed(1)).isEqualTo(2.2)
        .value(msg.alt.toFixed(1)).isEqualTo(3.3)
        .value(msg.quality).isEqualTo(100)
        .value(msg.satellites).isEqualTo(5)
        .value(msg.speed).isEqualTo(2);
      done();
    });
    parser.write(buf);
  });

  it('should parse telemetry', done => {
    let buf = new vanguard.Message(vanguard.TELEMETRY_SIZE, {
      type: vanguard.MSG_TYPE_TELEMETRY
    });

    let data = new BufferOffset(vanguard.TELEMETRY_SIZE);
    data.appendUInt32BE(2000);
    data.appendUInt8(1);
    data.appendUInt8(33);
    data.appendUInt16BE(512);
    data.appendFloatBE(30);
    data.appendFloatBE(50);
    data.appendFloatBE(-1);
    buf.setData(data);

    parser.on('data', msg => {
      test
        .value(msg.uptime).isEqualTo(2000)
        .value(msg.mode).isEqualTo(1)
        .value(msg.cpu).isEqualTo(33)
        .value(msg.freeMem).isEqualTo(512)
        .value(msg.intTemp).isEqualTo(30)
        .value(msg.intHumidity).isEqualTo(50)
        .value(msg.extTemp).isEqualTo(-1)
      done();
    });

    parser.write(buf);
  });

  it('should parse photo data', done => {
    let mockPhotoData = new Buffer([0x3, 0x5, 0x7, 0x9, 0x11,
                                    0x13, 0x15, 0x17, 0x19, 0x21]);

    let dataLength = vanguard.PHOTO_DATA_HEADER_SIZE + mockPhotoData.length;
    let buf = new vanguard.Message(dataLength, {
      type: vanguard.MSG_TYPE_PHOTO_DATA
    });
    let data = new BufferOffset(dataLength);
    data.appendUInt16BE(1);
    data.appendUInt16BE(2);
    data.appendUInt16BE(3);
    data.appendUInt32BE(4);
    data.append(mockPhotoData);
    buf.setData(data);

    parser.on('data', msg => {
      test
        .value(msg.index).isEqualTo(1)
        .value(msg.chunk).isEqualTo(2)
        .value(msg.chunkCount).isEqualTo(3)
        .value(msg.fileSize).isEqualTo(4)
        .value(mockPhotoData.length).isEqualTo(msg.data.length);

      for (let i = 0; i < mockPhotoData.length; i++) {
        test.value(mockPhotoData[i]).isEqualTo(msg.data[i]);
      }

      done();
    });

    parser.write(buf);
  });
  
  it('should parse program result', done => {
    let programName = new Buffer('helloworld');
    let programData = new Buffer('Helloworld!');
    let testBuf = new Buffer(programName);
    let dataLength = vanguard.PROGRAM_RESULT_HEADER_SIZE + programName.length + programData.length;
    let buf = new vanguard.Message(dataLength, {
      type: vanguard.MSG_TYPE_PROGRAM_RESULT
    });
    let data = new BufferOffset(dataLength);
    data.appendUInt16BE(0);
    data.appendUInt16BE(1);
    data.appendUInt16BE(1);
    data.appendUInt16BE(programName.length);
    data.appendUInt16BE(programData.length);
    data.appendInt8(0);
    data.append(programName);
    data.append(programData);
    buf.setData(data);

    parser.on('data', msg => {
      test
        .value(msg.index).isEqualTo(0)
        .value(msg.chunk).isEqualTo(1)
        .value(msg.chunkCount).isEqualTo(1)
        .value(msg.programNameLen).isEqualTo(programName.length)
        .value(msg.programDataLen).isEqualTo(programData.length)
        .value(msg.exitCode).isEqualTo(0)
        .value(msg.programName).isEqualTo(programName)
        .value(msg.programData === programData);

      done();
    });

    parser.write(buf);
  });
});
