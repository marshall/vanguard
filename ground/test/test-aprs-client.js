import * as aprs from '../lib/aprs';
import test from 'unit.js';
import net from 'net';
import sinon from 'sinon';
import { it, before, after, beforeEach, afterEach } from 'arrow-mocha/es5';

describe('APRS', () => {
  beforeEach(t => {
    t.sinon = sinon.sandbox.create();
  });

  afterEach(t => {
    t.sinon.restore();
  });

  afterEach(() => aprs.setCallsign(null));

  describe('callsign', () => {
    it('defaults to N0CALL', () => {
      test.value(aprs.callsign).isEqualTo('N0CALL');
    });

    it('setCallsign reverts to N0CALL when invalid', () => {
      aprs.setCallsign(null);
      test.value(aprs.callsign).isEqualTo('N0CALL');
    });

    it('setCallsign sets callsign', () => {
      aprs.setCallsign('ABCD-1');
      test.value(aprs.callsign).isEqualTo('ABCD-1');
    });
  });

  describe('Position', () => {
    let Position = aprs.Position;
    before(t => {
      t.packet = new Position({
        latitude: 12.20567,
        longitude: -123.20567,
        altitude: 500,
        time: new Date(Date.UTC(2015, 4, 21, 17, 2, 3))
      });
    });

    it('encodeTime', () => {
      let time = new Date(Date.UTC(2014, 1, 2, 23, 45, 33));
      test.value(Position.encodeTime(time)).isEqualTo('234533h')
    });

    it('encodeLatitude', () => {
      test
        .value(Position.encodeLatitude(12.20567)).isEqualTo('1212.34N')
        .value(Position.encodeLatitude(-12.20567)).isEqualTo('1212.34S')
        .value(Position.encodeLatitude(0.0)).isEqualTo('0000.00N')
    });

    it('encodeLongitude', () => {
      test
        .value(Position.encodeLongitude(123.20567)).isEqualTo('12312.34E')
        .value(Position.encodeLongitude(-123.20567)).isEqualTo('12312.34W')
        .value(Position.encodeLongitude(0.0)).isEqualTo('00000.00E')
    });

    it('getData', t => {
      test
        .value(t.packet.getData())
        .isEqualTo('/170203h1212.34N/12312.34WO000/000/A=000500');
    });

    it('toString', t => {
      test
        .value(t.packet.toString())
        .isEqualTo('N0CALL>APRS,TCPIP*:/170203h1212.34N/12312.34WO000/000/A=000500');
    });
  });

  describe('Client', () => {
    beforeEach(t => {
      t.client = new aprs.Client();
      t.connect = t.client._socket.connect = test.spy();
      t.write = t.client._socket.write = test.spy();
    });

    it('defaults are set', t => {
      test
        .value(t.client.state).isEqualTo('disconnected')
        .value(t.client.verified).isEqualTo(false)
        .value(t.client.name).isEqualTo('vanguard-aprs-client')
        .value(t.client.version).isEqualTo('0.0.1')
    });

    it('parses server info', (t, done) => {
      t.client.on('server-info', info => {
        test
          .value(t.client.state).isEqualTo('need-login')
          .value(info.softwareName).isEqualTo('name')
          .value(info.softwareVersion).isEqualTo('version')
        done();
      });

      t.client.parse('# name version\r\n');
    });

    it('sends raw messages', (t, done) => {
      t.client.on('message', msg => {
        test.value(msg).isEqualTo('abc');
        done();
      });
      t.client.parse('abc\r\n');
    });

    describe('login response', () => {
    });

    it('sendLine adds \\r\\n', t => {
      t.client._socket.write = test.spy();
      t.client.sendLine('abcd');
      test.assert(t.client._socket.write.withArgs('abcd\r\n').calledOnce);
    });


    it('connect defaults', t => {
      t.client.connect();
      test.assert(t.connect.withArgs(14580, 'noam.aprs2.net').calledOnce);
    });

    it('emits connect', (t, done) => {
      t.client.connect();
      t.client.on('connect', done);
      t.client._socket.emit('connect');
    });

    describe('login', () => {
      it('waitForLogin resolves after emitting server-info', t => {
        t.client.state = 'connected';
        process.nextTick(() => t.client.emit('server-info'));

        return test.promise
          .given(t.client.waitForLogin())
          .then(() => test.value(t.client.state, 'need-login'))
          .catch(err => test.fail(err.message));
      });

      it('waitForLogin resolves immediately when state=need-login', t => {
        t.client.state = 'need-login';
        return test.promise
          .given(t.client.waitForLogin())
          .catch(err => test.fail(err.message));
      });

      function loginTest(t, expected, response, ...args) {
        process.nextTick(() => {
          t.client.parse(response);
        });

        t.client.state = 'need-login';
        return test.promise
          .given(t.client.login(...args))
          .then(() => {
            test.value(t.write.lastCall.args[0]).isEqualTo(expected);
          })
          .catch(err => {
            console.error(t.write.lastCall.args[0], expected);
            test.fail(err.message)
          });
      }

      it('login line w/ defaults', t => {
        return loginTest(t,
                 'user N0CALL pass -1 vers vanguard-aprs-client 0.0.1\r\n',
                 '# logresp N0CALL unverified, server SCALL\r\n');
      });

      it('login w/ custom user and pass', t => {
        return loginTest(t,
                 'user ABC pass 123 vers vanguard-aprs-client 0.0.1\r\n',
                 '# logresp ABC verified, server SCALL\r\n',
                 'ABC', '123');
      });

      it('login w/ filter', t => {
        return loginTest(t,
                 'user N0CALL pass -1 vers vanguard-aprs-client 0.0.1 filter XYZ\r\n',
                 '# logresp N0CALL verified, server SCALL\r\n',
                 null, null, 'XYZ');
      });

      it('parses verified response', (t, done) => {
        t.client.on('login', () => {
          test
            .value(t.client.state).isEqualTo('ready')
            .value(t.client.verified).isEqualTo(true)
            .value(t.client.serverInfo.callsign).isEqualTo('SCALL')
          done();
        });
        t.client.parse('# logresp N0CALL verified, server SCALL\r\n');
      });

      it('parses unverified response', (t, done) => {
        t.client.on('login', () => {
          test
            .value(t.client.state).isEqualTo('ready')
            .value(t.client.verified).isEqualTo(false)
            .value(t.client.serverInfo.callsign).isEqualTo('SCALL')
          done();
        });
        t.client.parse('# logresp N0CALL unverified, server SCALL\r\n');
      });
    });
  });
});
