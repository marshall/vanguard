import _ from 'lodash';
import blessed from 'blessed';
import { sprintf } from 'sprintf-js';

import { Pane, Table } from './pane';

const LAT_FORMAT = '%+8.4f';
const LON_FORMAT = '%+9.4f';
const ALT_FORMAT = '%05.2f km';
const SPEED_FORMAT = '%03d   km/h';

class Position extends Pane {
  constructor() {
    super();
    this.position = {};
  }

  initUI() {
    this.setLabel('Position');

    this.table = this.add(Table, {
      tags: true,
      rows: [
        ['{white-fg}Latitude{/}', '??'],
        ['{white-fg}Longitude{/}', '??'],
        ['{white-fg}Altitude{/}', '??'],
        ['{white-fg}Speed{/}', '??']
      ],
      align: 'left'
    });

    this.on('location', position => {
      _.merge(this.position, position);

      let lat = sprintf(LAT_FORMAT, this.position.lat);
      let lon = sprintf(LON_FORMAT, this.position.lon);
      let alt = sprintf(ALT_FORMAT, this.position.alt / 1000.0);
      let speed = sprintf(SPEED_FORMAT, this.position.speed);

      this.table.setColumn(1, [lat, lon, alt, speed]);
      this.table.renderData();
    });
  }
}

new Position();
