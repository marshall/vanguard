import repl from 'repl';
import net from 'net';

import _ from 'lodash';
import otaat from 'otaat-repl';

import log from './log';

export class GroundREPLServer {
  constructor(station, ...args) {
    this.station = station;
    this.session = otaat.start(...args);
    this.session.on('reset', () => this.reset());
    this.reset();
  }

  reset() {
      let ctx = this.session.context;

    _.extend(this.session.context, {
      station: this.station,
      last_message: type => this.station.getLastMessage(type),
      ping: magic => {
        magic = magic || _.random(Math.pow(2, 15) - 1, false);
        ctx.console.log('ping', magic);
        return this.station.ping(magic);
      },
      upload: path => this.station.upload(path)
    });

    ['location', 'telemetry', 'photo_data', 'pong'].forEach(msgType => {
      this.session.context['last_' + msgType] = () => this.station.getLastMessage(_.camelCase(msgType));
    });
  }
}

export class GroundREPLNetServer extends net.Server {
  constructor(station) {
    super(socket => this.startREPL(socket));
    this.station = station;
  }

  startREPL(socket) {
    log.info('[%s] REPL connected', socket.remoteAddress);
    let replServer = new GroundREPLServer(this.station, {
      prompt: 'vanguard|' + socket.remoteAddress + '> ',
      input: socket,
      output: socket,
      terminal: true,
      useGlobal: false
    });

    replServer.session.on('exit', () => {
      log.info('[%s] REPL disconnected', socket.remoteAddress);
      socket.end();
    });
  }
}

export function listen(station, ...args) {
  let server = new GroundREPLNetServer(station);
  server.listen(...args);
  return server;
}
