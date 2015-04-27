require('babel/register');

import { install } from 'source-map-support';
install();

import program from 'commander';
import { Station } from './lib/station';
import log from './lib/log';

program
  .version('0.0.1')
  .option('-r, --radio <device>', 'Radio UART device name, or - for STDIN [detect]')
  .option('-rb, --radio-baud <baudrate>', 'Radio baudrate [9600]', '9600')
  .option('-g, --gps <device>', 'GPS UART device name [none]')
  .option('-gb, --gps-baud <baudrate>', 'GPS baudrate [9600]', '9600')
  .option('-u, --remote-url <address>', 'Remote CouchDB base URL to sync with')
  .option('-v, --verbose', 'Enable verbose logging', false)
  .parse(process.argv);

log.setVerbosity(program.verbose ? 1 : 0);

log.info('new station');
var station = new Station(program);
log.info('start');
station.start();
