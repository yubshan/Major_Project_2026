# Requirement / Purpose: Generates static, predefined sensor packets (e.g., simulating a tight corridor or an obstacle right in
#  front of the nose).


# Creates an 8x8 ToF sensor grid where every cell
# contains the same distance value in millimeters.
def create_tof_grid(value):
    return [[value] * 8 for _ in range(8)]


# Returns a fake sensor packet for a given test scenario.
# The packet follows the same format defined in shared/sensor_format.py

def get_mock_sensor_packet(scenario):
    
    if scenario == "open_front":
        return {
            "us_front": 200,
            "us_left45": 200,
            "us_left90": 200,
            "us_right45": 200,
            "us_right90": 200,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }
    
    elif scenario == "obstacle_ahead":
        return {
            "us_front": 30,
            "us_left45": 200,
            "us_left90": 200,
            "us_right45": 200,
            "us_right90": 200,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }

    elif scenario == "narrow_corridor":
        return {
            "us_front": 200,
            "us_left45": 40,
            "us_left90": 30,
            "us_right45": 40,
            "us_right90": 30,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }
    
    elif scenario == "left_blocked":
        return {
            "us_front": 200,
            "us_left45": 30,
            "us_left90": 20,
            "us_right45": 200,
            "us_right90": 200,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }
    
    elif scenario == "right_blocked":
        return {
            "us_front": 200,
            "us_left45": 200,
            "us_left90": 200,
            "us_right45": 30,
            "us_right90": 20,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }
    
    elif scenario == "all_blocked":
        return {
            "us_front": 20,
            "us_left45": 20,
            "us_left90": 20,
            "us_right45": 20,
            "us_right90": 20,
            "tof_grid": create_tof_grid(500),
            "timestamp": 0
        }
    
    #handle an unknown scenario
    else:
        raise ValueError(f"Unknown scenario: {scenario}")