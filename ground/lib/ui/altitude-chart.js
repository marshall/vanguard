import blessed from 'blessed';
import contrib from 'blessed-contrib';
import moment from 'moment';
import { sprintf } from 'sprintf-js';

import { Pane } from './pane';

const UPTIME_SHORT_FORMAT = '%02d:%02d';

class AltitudeChart extends Pane {
  initUI() {
    this.setLabel('Altitude (km)');
    this.data = {
      title: 'altitude',
      x: [],
      y: []
    };

    this.chart = new contrib.line({});
    this.lastUpdate = moment.duration(0);
    this.main.append(this.chart);

    this.on('telemetry', t => { this.uptime = t.uptime; });
    this.on('location', p => this.onPosition(p));
  }

  onPosition(position) {
    let uptime = moment.duration(this.uptime || 0, 'seconds');
    let uptimeCopy = moment.duration(uptime.asMilliseconds());
    if (uptimeCopy.subtract(this.lastUpdate).asSeconds() < 10) {
      return;
    }

    this.lastUpdate = uptime;
    let uptimeStr = sprintf(UPTIME_SHORT_FORMAT, uptime.hours(),
                            uptime.minutes());

    this.data.x.push(uptimeStr);
    this.data.y.push(position.alt);
    this.chart.setData([this.data]);
    this.screen.render();
  }
}
new AltitudeChart();
