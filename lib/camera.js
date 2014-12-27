var path = require('path'),
    spawn = require('child_process').spawn,
    temp = require('temp');

temp.track();

function Camera() {
  this.device = '/dev/video0';
  this.dir = temp.mkdirSync('vanguard');
};

Camera.prototype = {
  takePhoto: function(callback) {
    var outfile = temp.path({ dir: this.dir, suffix: '.jpeg' });
    var proc = spawn('streamer', [this.device, '-b', '24', '-o', outfile]);
    proc.on('close', function(code) {
      callback(outfile);
    });
  }
};

module.exports = new Camera();
