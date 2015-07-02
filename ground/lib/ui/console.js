#!/usr/bin/env node

require("babel/polyfill");

import { install } from 'source-map-support';
install();

import path from 'path';

import _ from 'lodash';
import shell from 'shelljs';
import winston from 'winston';
import program from 'commander';

import { VgStation } from '../../vg-station';

const TIME = require.resolve('./time');
const POSITION = require.resolve('./position');
const STATS = require.resolve('./stats');
const ALT_CHART = require.resolve('./altitude-chart');
const TEMP_CHART = require.resolve('./temp-chart');
const REPL_CLIENT = require.resolve('../repl-client');
const STATION = require.resolve('../../vg-station');

export class Console {
  constructor(options, stationArgv) {
    _.merge(this, _.defaults(options || {}, {
      session: 'vg-console',
      cwd: path.join(__dirname, '../../'),
      base: 0
    }));

    stationArgv = stationArgv || [];
    stationArgv.unshift(STATION);

    this.buildPanes(new Map([
      ['telemetry', { height: 15, cols: new Map([
        ['time', { width: 33, cmd: [TIME] }],
        ['position', { width: 33, cmd: [POSITION] }],
        ['stats', { width: 33, cmd: [STATS]  }],
      ])}],
      ['charts', { height: 30, cols: new Map([
        ['alt', { width: 50, cmd: [ALT_CHART] }],
        ['temp', { width: 50, cmd: [TEMP_CHART] }],
      ])}],
      ['repl', { height: 35, cmd: [REPL_CLIENT] }],
      ['station', { height: 20, cmd: stationArgv, fallback: process.env.SHELL }]
    ]));

    this.tmuxCmd = shell.which('tmux');
    this.nodeCmd = process.execPath;
  }

  buildPanes(layout) {
    let panes = [];
    let height = 100;

    for (var [name, opts] of layout.entries()) {
      let pane = [name, opts];
      if (opts.cols) {
        let cols = opts.cols.entries();
        pane = cols.next().value;
        pane[1].height = opts.height;
      }

      pane[1].index = panes.length;
      pane[1].relativeTo = panes.length - 1;
      pane[1].split = 'v';
      if (panes.length > 0) {
        let lastRow = panes[panes.length - 1];
        let newHeight = height - lastRow[1].height;
        pane[1].splitSize = Math.round((newHeight / height) * 100);
        height = newHeight;
      }

      panes.push(pane);
    }

    // Now loop through again to get leftover columns in each row
    for (var opts of layout.values()) {
      let width = 100;
      if (!opts.cols) {
        continue;
      }

      let cols = [...opts.cols];
      let lastPane = cols.shift();
      for (var pane of cols) {
        pane[1].index = panes.length;
        pane[1].relativeTo = lastPane[1].index;
        pane[1].split = 'h';
        let newWidth = width - lastPane[1].width;
        pane[1].splitSize = Math.round((newWidth / width) * 100);

        panes.push(pane);
        lastPane = pane;
        width = newWidth;
      }
    }

    this.panes = new Map(panes);
  }

  quote(s) {
    return '"' + s.replace(/"/g, '\\"') + '"';
  }

  tmux(...args) {
    let cmd = args.join(' ');
    console.log(cmd);
  }

  getPaneIndex(pane) {
    return this.panes.get(pane).index + this.base;
  }

  genPanes() {
    for (let [name, pane] of this.panes) {
      let cmd;

      if (pane.index === 0) {
        let session = this.quote(this.session);
        cmd = ['new-session', '-d', '-n', session, '-s', session];
      } else {
        cmd = ['split-window', '-t', pane.relativeTo + this.base,
               '-' + pane.split, '-p', pane.splitSize];
      }

      let paneCmd = [this.nodeCmd, ...pane.cmd].map(this.quote).join(' ');
      paneCmd += ' || ' + (pane.fallback ||
                          'echo "failed to run ' + pane.cmd[0] + '" && sleep 100');

      cmd.push('-c', this.quote(this.cwd), this.quote(paneCmd));
      this.tmux(...cmd);
    }
  }

  generate() {
    this.genPanes();
    this.tmux('select-pane', '-t', this.getPaneIndex('repl'));
  }
}

export function main(argv) {
  program.version('0.0.1')
         .option('-b, --base <index>', 'tmux pane base index', parseInt, 0)
         .option('-s, --session <name>', 'session name', 'vg-console')
         .option('-c, --cwd <dir>', 'working directory')
         .allowUnknownOption(true);

  program.on('--help', () => {
    console.log('  Ground station options:');
    console.log('');
    console.log(new VgStation().optionHelp().replace(/^/gm, '    '));
  });

  let parsed = program.parseOptions(program.normalize(argv.slice(2)));
  program.args = parsed.args;
  program.parseArgs(program.args, parsed.unknown);

  new Console(program, parsed.unknown).generate();
}

if (require.main === module) {
  main(process.argv)
}
