import _ from 'lodash';
import blessed from 'blessed';
import { sprintf } from 'sprintf-js';

import { Pane, Table } from './pane';

const CPU_FORMAT = '%3d %%';
const FREEMEM_FORMAT = '%3d MB';
const TEMP_FORMAT = '%+5.1f C';

class Stats extends Pane {
  initUI() {
    this.setLabel('Stats');

    this.table = this.add(Table, {
      tags: true,
      height: 'shrink',
      rows: [
        ['{white-fg}CPU Usage{/}', '??'],
        ['{white-fg}Free Mem{/}', '??'],
        ['{white-fg}Int. Temp{/}', '??'],
        ['{white-fg}Ext. Temp{/}', '??']
      ],
      align: 'left'
    });

    this.on('telemetry', telemetry => {
      let cpu = sprintf(CPU_FORMAT, telemetry.cpu);
      let freeMem = sprintf(FREEMEM_FORMAT, telemetry.freeMem);
      let intTemp = sprintf(TEMP_FORMAT, telemetry.intTemp);
      let extTemp = sprintf(TEMP_FORMAT, telemetry.extTemp);

      this.table.setColumn(1, [cpu, freeMem, intTemp, extTemp]);
      this.table.renderData();
    });
  }
}

new Stats();
