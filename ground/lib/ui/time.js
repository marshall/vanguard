import blessed from 'blessed';
import moment from 'moment';
import { sprintf } from 'sprintf-js';

import { Pane, Table } from './pane';

const UNKNOWN = '??';
const DATE_FORMAT = 'MM/DD/YYYY HH:mm:ss';
const UPTIME_FORMAT = '%02dh %02dm %02ds';

class Time extends Pane {
  constructor() {
    super();
    this.lastMsgTime = this.balloonTime = null;
  }

  initUI() {
    this.setLabel('Time');

    this.table = this.add(Table, {
      tags: true,
      rows: [
        ['{white-fg}System{/}', '??'],
        ['{white-fg}Balloon{/}', '??'],
        ['{white-fg}LastMsg{/}', '??'],
        ['{white-fg}Uptime{/}', '??']
      ],
      align: 'left'
    });

    this.on('telemetry', t => this.onTelemetry(t));
  }

  onMessage(msg) {
    super.onMessage(msg);
    this.lastMsgTime = moment();

    let balloonTime = moment.unix(msg.timestamp).format(DATE_FORMAT);

    this.table.rows[1][1] = balloonTime;
    this.table.renderData();
  }

  onTelemetry(telemetry) {
    this.uptime = telemetry.uptime;
    if (!telemetry.uptime) {
      return;
    }

    let uptime = moment.duration(telemetry.uptime, 'seconds');
    let uptimeStr = sprintf(UPTIME_FORMAT, uptime.hours(), uptime.minutes(),
                            uptime.seconds());
    this.table.rows[3][1] = uptimeStr;
    this.table.renderData();
  }

  start() {
    this.startInterval(1000);
  }

  update() {
    let systemTime = moment().format(DATE_FORMAT);
    this.table.rows[0][1] = systemTime;

    let lastMsgTime = UNKNOWN;
    if (this.lastMsgTime) {
      let duration = moment.duration(this.lastMsgTime.diff(moment()));
      lastMsgTime = duration.humanize(true);
    }

    this.table.rows[2][1] = lastMsgTime;
    this.table.renderData();
  }
}

new Time();
