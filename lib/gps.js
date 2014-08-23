var gpsd = require('node-gpsd');

function GPS() {
  this.lat = 0;
  this.lon = 0;
  this.alt = 0;
  this.time = null;
  this.speed = 0;

  this.daemon = null;
  this.listener = null;
}

GPS.prototype = {
  handleTPV: function(data) {
    switch (data.tag) {
      case 'RMC':
      case 'GGA':
        this.handleLocation(data);
        break;
    }
  },

  handleLocation: function(data) {
    this.lat = data.lat;
    this.lon = data.lon;
    this.alt = data.alt;

    if (data.speed) {
      this.speed = data.speed;
    }

    if (data.time) {
      this.time = data.time;
    }

    console.log(data.lat, data.lon, data.alt);
  },

  start: function(options) {
    options = options || {};
    if (!options.device) {
      options.device = '/dev/ttyAMA0';
    }

    var self = this;
    this.daemon = new gpsd.Daemon(options);
    this.daemon.start(function() {
      self.listener = new gpsd.Listener();
      self.listener.connect(function() {
        self.listener.on('TPV', self.handleTPV.bind(self));
      });
      self.listener.watch();
    });
  },

  stop: function() {
    if (this.listener) {
      this.listener.unwatch();
    }

    if (this.daemon) {
      this.daemon.stop();
    }
  }
};

module.exports = new GPS();
