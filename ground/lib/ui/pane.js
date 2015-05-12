import util from 'util';

import _ from 'lodash';
import blessed from 'blessed';
import Listener from './listener';

export class Pane extends Listener {
  constructor() {
    super();
    this.screen = blessed.screen({
      autoPadding: true,
      smartCSR: true,
    });

    this.label = blessed.box({
      parent: this.screen,
      tags: true,
      width: '100%',
      height: 1
    });

    this.main = blessed.box({
      parent: this.screen,
      top: 1,
      width: '100%',
      height: '100%-1'
    });

    this.initUI();
    this.screen.render();
    this.start();
  }

  add(type, options) {
    options = _.defaults(options || {}, {
      parent: this.main
    });

    return new type(options);
  }

  setLabel(label) {
    this.label.setContent('{center}{green-fg}{underline}' + label + '{/}');
  }

  initUI() {
  }

  update() {
  }

  handleUpdate() {
    this.update();
    this.screen.render();
  }

  start() {
  }

  startInterval(interval) {
    this.updateTimer = setInterval(() => this.handleUpdate(), interval);
  }

  stop() {
    if (this.updateTimer) {
      clearInterval(this.updateTimer);
    }
  }
}

export class Table extends blessed.Table {
  setColumn(i, rowData) {
    this.rows.forEach((row, r) => {
      row[i] = rowData[r];
    });
  }

  setContent(content, ...args) {
    let c = content || '';
    return super.setContent(c.replace(/\n\n/g, '\n'), ...args);
  }

  renderData() {
    this.setData(this.rows);
    this.screen.render();
  }

}
