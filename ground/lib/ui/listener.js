import net from 'net';

import _ from 'lodash';
import { EventEmitter } from 'events';
import nlj from 'newline-json';

const CONNECT_RETRY = 5000;

export default class Listener extends EventEmitter {
  constructor() {
    super();
    console.log('Waiting for ground station to be ready on port 41001');
    this.connect();
  }

  connect() {
    this.socket = net.connect(41001, () => {
      let parser = new nlj.Parser();
      parser.on('data', msg => this.onMessage(msg));
      this.socket.pipe(parser);
      this.emit('connect');
    });

    this.socket.on('error', err => {
      this.socket = null;
      setTimeout(() => this.connect(), CONNECT_RETRY);
    });

    this.socket.on('end', () => {
      this.socket = null;
      this.emit('disconnect');
      setTimeout(() => this.connect(), CONNECT_RETRY);
    });
  }

  send(data) {
    this.socket.write(JSON.stringify(data) + '\n');
  }

  onMessage(msg) {
    let type = msg.type;
    if (!type) {
      return;
    }

    this.emit(type, msg);
    /*let handler = this[_.camelCase('on ' + type)];
    if (!handler) {
      return;
    }

    handler.call(this, msg);*/
  }
}
