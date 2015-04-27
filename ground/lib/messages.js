import _ from 'lodash';

export class Location {
  constructor(options) {
    options = _.defaults(options, {
      lat: 0,
      lon: 0,
      alt: 0,
      satellites: 0,
      speed: 0,
      quality: 0,
      timestamp: 0,
      type: 'location'
    });

    _.merge(this, options, (a, b, key) => {
      if (!_.includes(['lat', 'lon', 'alt'], key)) {
        return undefined;
      }

      return _.isString(b) ? parseFloat(b) : undefined;
    });
  }
};

export class Telemetry {
  constructor(options) {
    _.merge(this, _.defaults(options, {
      uptime: 0,
      mode: 0,
      cpu: 0,
      freeMem: 0,
      intTemp: 0,
      intHumidity: 0,
      extTemp: 0,
      type: 'telemetry'
    }));
  }
}

export class PhotoData {
  constructor(options) {
    _.merge(this, _.defaults(options, {
      index: -1,
      chunk: -1,
      chunkCount: -1,
      fileSize: -1,
      data: null,
      type: 'photo-data'
    }));
  }
}
