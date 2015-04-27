import winston from 'winston';
winston.cli();

var logger = new winston.Logger({
  transports: [
    new winston.transports.File({
      filename: '/var/log/vanguard-station.log',
      level: 'debug',
      timestamp: true
    }),
    new winston.transports.Console({
      colorize: true,
      level: 'info'
    })
  ]
});

logger.setVerbosity = function(verbosity) {
  if (verbosity >= 1) {
    logger.transports.console.level = 'debug';
  }
}

export { logger as default };
