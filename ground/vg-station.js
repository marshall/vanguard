#!/usr/bin/env node
require('babel/register');

import { install } from 'source-map-support';
install();

import commander from 'commander';
import { Station } from './lib/station';
import log from './lib/log';

export class VgStation extends commander.Command {
  constructor() {
    super();
    this.version('0.0.1')
        .option('-r, --radio <device>', 'Radio UART device name, or - for STDIN [detect]')
        .option('-rb, --radio-baud <baudrate>', 'Radio baudrate [9600]', '9600')
        .option('-g, --gps <device>', 'GPS UART device name [none]')
        .option('-gb, --gps-baud <baudrate>', 'GPS baudrate [9600]', '9600')
        .option('-u, --remote-url <address>', 'Remote CouchDB base URL to sync with')
        .option('-v, --verbose', 'Enable verbose logging', false)
        .option('-m, --mock', 'Use mock balloon', false);
  }
}

export function main(argv) {
  let program = new VgStation();
  program.parse(argv);
  log.setVerbosity(program.verbose ? 1 : 0);

  let station = new Station(program);
  station.start();
}

if (require.main === module) {
  main(process.argv);
}
