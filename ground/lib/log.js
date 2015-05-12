import bunyan from 'bunyan';
import winston from 'winston';
winston.cli();

class WinstonStream {
  write(rec) {
    let level = bunyan.nameFromLevel[rec.level].toLowerCase();
    let msg = rec.msg;
    delete rec.msg;
    delete rec.v;
    delete rec.level;

    winston.log(level, msg, rec);
  }
}

function bufferSerializer(buf) {
  if (!(buf instanceof Buffer)) {
    return buf;
  }
  return { length: buf.length, data: buf.toString('base64') }
}

var logger = bunyan.createLogger({
  name: 'station',
  serializers: {
    data: bufferSerializer
  },
  streams: [{
    path: '/tmp/vg-station.log',
    level: 'debug'
  }, {
    level: 'info',
    type: 'raw',
    stream: new WinstonStream()
  }]
});

logger.setVerbosity = function(verbosity) {
  if (verbosity >= 1) {
    winston.default.transports.console.level = 'debug';
    logger.levels(1, 'DEBUG');
  }
}

export { logger as default };
