import blessed from 'blessed';
import contrib from 'blessed-contrib';
import moment from 'moment';
import { sprintf } from 'sprintf-js';

import { Pane } from './pane';

const UPTIME_SHORT_FORMAT = '%02d:%02d';

class TempChart extends Pane {
  initUI() {
    this.setLabel('Temperature (C)');
    this.data = [{
      title: 'Int',
      style: { line: 'red' },
      x: [],
      y: [],
    }, {
      title: 'Ext',
      style: { line: 'blue' },
      x: [],
      y: []
    }];

    this.chart = new contrib.line({ showLegend: true });
    this.lastUpdate = moment.duration(0);
    this.main.append(this.chart);

    this.on('telemetry', t => this.onTelemetry(t));
  }

  onTelemetry(telemetry) {
    let uptime = moment.duration(telemetry.uptime || 0, 'seconds');
    let uptimeCopy = moment.duration(uptime.asMilliseconds());
    if (uptimeCopy.subtract(this.lastUpdate).asSeconds() < 30) {
      return;
    }

    this.lastUpdate = uptime;
    let uptimeStr = sprintf(UPTIME_SHORT_FORMAT, uptime.hours(),
                            uptime.minutes());

    this.data[0].x.push(uptimeStr);
    this.data[0].y.push(telemetry.intTemp);
    this.data[1].x.push(uptimeStr);
    this.data[1].y.push(telemetry.extTemp);
    this.chart.setData(this.data);
    this.screen.render();
  }
}
new TempChart();
