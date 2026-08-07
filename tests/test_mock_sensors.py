import unittest

from shared.mock_sensors import get_mock_sensor_packet
from shared.sensor_format import validate_sensor_packet


class TestMockSensors(unittest.TestCase):

    def test_all_scenarios_produce_valid_packets(self):
        scenarios = [
            "open_front",
            "obstacle_ahead",
            "narrow_corridor",
            "left_blocked",
            "right_blocked",
            "all_blocked",
        ]

        for scenario in scenarios:
            packet = get_mock_sensor_packet(scenario)

            self.assertTrue(
                validate_sensor_packet(packet),
                f"Invalid packet for scenario: {scenario}"
            )


if __name__ == "__main__":
    unittest.main()