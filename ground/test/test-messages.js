import messages, { Location } from '../lib/messages';
import test from 'unit.js';

describe('messages', () => {
  describe('Location', () => {
    it('should parse string lat/lon/alt', () => {
      let l = new Location({ lat: '22.7', lon: '44.33', alt: '100.1' });
      test
        .value(l.lat).isEqualTo(22.7)
        .value(l.lon).isEqualTo(44.33)
        .value(l.alt).isEqualTo(100.1)
    });
  });
});

export function testLocation(test) {
}
