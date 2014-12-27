var camera = require('./lib/camera'),
    gps = require('./lib/gps');

gps.start();
camera.takePhoto(function(photoPath) {
  console.log('Photo taken at', photoPath);
});
