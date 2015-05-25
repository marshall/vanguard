from cStringIO import StringIO
import os
import struct
import sys
import unittest

import mock

top_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(top_dir)

from vanguard.protocol import vanguard as proto
from vanguard import hab_utils

class MsgReaderTest(unittest.TestCase):
    def test_bad_start_marker(self):
        reader = proto.MsgReader()
        data = StringIO('\xff' * proto.Msg.header_end)
        self.assertRaises(proto.BadMarker, lambda: reader.read(data))

    def test_bad_msg_type(self):
        reader = proto.MsgReader()
        data = StringIO('\xa3\x9a' + ('\xff' * proto.Msg.header_end))
        self.assertRaises(proto.BadMsgType, lambda: reader.read(data))

    def test_bad_checksum(self):
        reader = proto.MsgReader()
        data = StringIO('\xa3\x9a' + \
                        struct.pack('!LBB', 0,
                                           proto.LocationMsg.TYPE,
                                           proto.LocationMsg.data_struct.size) + \
                        ('\xff' * 4) + \
                        ('\xff' * proto.LocationMsg.data_struct.size) + \
                        '\x9b\x92')

        self.assertRaises(proto.BadChecksum, lambda: reader.read(data))
        self.assertEqual(reader.state, reader.state_header)

    def test_bad_end_marker(self):
        reader = proto.MsgReader()
        data_bytes = '\xff' * proto.LocationMsg.data_struct.size
        data_crc = hab_utils.crc32(data_bytes)
        data = StringIO('\xa3\x9a' + \
                        struct.pack('!LBBL', 0,
                                             proto.LocationMsg.TYPE,
                                             proto.LocationMsg.data_struct.size,
                                             data_crc) + \
                        data_bytes + \
                        '\xff\xff')

        self.assertRaises(proto.BadMarker, lambda: reader.read(data))

class LocationMsgTest(unittest.TestCase):
    def setUp(self):
        self.location_data = proto.LocationMsg.data_struct.pack(1.1, 2.2, 3.3, 100, 5, 2)
        self.data = proto.Msg.marker_struct.pack(proto.Msg.begin) + \
               proto.Msg.header_struct.pack(0, proto.LocationMsg.TYPE,
                                            proto.LocationMsg.data_struct.size,
                                            hab_utils.crc32(self.location_data)) + \
               self.location_data + \
               proto.Msg.marker_struct.pack(proto.Msg.end)

    def test_reader(self):
        reader = proto.MsgReader()
        for i in range(0, 10):
            msg = reader.read(StringIO(self.data))
            self.assertNotEqual(msg, None)
            self.assertAlmostEqual(msg.latitude, 1.1)
            self.assertAlmostEqual(msg.longitude, 2.2)
            self.assertAlmostEqual(msg.altitude, 3.3)
            self.assertEqual(msg.quality, 100)
            self.assertEqual(msg.satellites, 5)
            self.assertEqual(msg.speed, 2)
            self.assertSequenceEqual(msg.as_buffer(), self.data)

    @mock.patch('time.time', mock.MagicMock(return_value=0))
    def test_build(self):
        location_msg = proto.LocationMsg.from_data(latitude=1.1, longitude=2.2,
                                                   altitude=3.3, quality=100,
                                                   satellites=5, speed=2)
        self.assertSequenceEqual(location_msg.as_buffer(), self.data)

class PingMsgTest(unittest.TestCase):
    def setUp(self):
        self.ping_data = proto.PingMsg.data_struct.pack(0x1234)
        self.data = proto.Msg.marker_struct.pack(proto.Msg.begin) + \
                    proto.Msg.header_struct.pack(0, proto.PingMsg.TYPE,
                                                 proto.PingMsg.data_struct.size,
                                                 hab_utils.crc32(self.ping_data)) + \
                    self.ping_data + \
                    proto.Msg.marker_struct.pack(proto.Msg.end)

    @mock.patch('time.time', mock.MagicMock(return_value=0))
    def runTest(self):
        msg = proto.PingMsg.from_data(magic=0x1234)
        self.assertSequenceEqual(msg.as_buffer(), self.data)

if __name__ == '__main__':
    unittest.main()
