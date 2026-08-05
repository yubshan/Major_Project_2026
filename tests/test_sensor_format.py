import unittest

from shared.sensor_format import (validate_sensor_packet)

class TestSensorFormat(unittest.TestCase):

    def test_valid_packet(self):
        packet = {
            "us_front": 100,
            "us_left45": 150,
            "us_left90": 200,
            "us_right45": 250,
            "us_right90": 300,
            "tof_grid": [[500] * 8 for _ in range(8)],
            "timestamp": 1234567890
        }
        self.assertTrue(validate_sensor_packet(packet))

    def test_invalid_packet_missing_field(self):
        packet = {
            "us_front": 100,
            "us_left45": 150,
            "us_left90": 200,
            "us_right45": 250,
            "timestamp": 1234567890
        }
        self.assertFalse(validate_sensor_packet(packet))

    def test_invalid_packet_negative_value(self):
        packet = {
            "us_front": 100,
            "us_left45": 150,
            "us_left90": 200,
            "us_right45": 250,
            "us_right90": -300,
            "tof_grid": [[0] * 8 for _ in range(8)],
            "timestamp": 1234567890
        }
        self.assertFalse(validate_sensor_packet(packet))

    def test_invalid_packet_tof_grid(self):
        packet = {
            "us_front": 100,
            "us_left45": 150,
            "us_left90": 200,
            "us_right45": 250,
            "us_right90": 300,
            "tof_grid": [[0] * 7 for _ in range(8)],
            "timestamp": 1234567890
        }
        self.assertFalse(validate_sensor_packet(packet))

if __name__ == "__main__":
    unittest.main()
