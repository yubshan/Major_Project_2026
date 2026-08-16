# modules/decision_logic/behavior_tree/navigate_to_target.py
#
# NavigateToTarget — Behavior Tree node (Priority 3)
#
# Reads the active navigation waypoint from the blackboard.
# If a waypoint exists and the robot is not already there:
#   - Computes a simple steering command (left/right/forward) toward the waypoint
#   - Writes the motor command to "state/motor_command"
#   - Returns RUNNING (still navigating)
#
# If no waypoint is set, or the robot has reached it:
#   - Clears the waypoint
#   - Returns FAILURE (let Selector fall through to RLExplore)

import math
import py_trees
from shared.coordinate_system import world_to_grid, grid_to_world

ARRIVAL_RADIUS_CELLS = 2    # cells — considered "arrived" within this range
NAV_SPEED            = 130  # motor speed during navigation


def _cells_distance(r1, c1, r2, c2) -> float:
    return math.sqrt((r2 - r1) ** 2 + (c2 - c1) ** 2)


def _steer_toward(robot_pose: dict, target_row: int, target_col: int) -> dict:
    """
    Simple proportional steering toward a grid cell.
    Returns a motor command dict.
    """
    target_x, target_y  = grid_to_world(target_row, target_col)

    # Angle to target in world coordinates
    dx = target_x - robot_pose["x"]
    dy = target_y - robot_pose["y"]
    angle_to_target = math.degrees(math.atan2(dy, dx))

    # Heading error (how much to turn)
    heading_error = angle_to_target - robot_pose.get("heading", 0.0)
    # Normalise to [-180, 180]
    heading_error = (heading_error + 180) % 360 - 180

    if abs(heading_error) < 20:
        # Mostly aligned — go forward
        return {"left_speed": NAV_SPEED, "right_speed": NAV_SPEED, "duration_ms": 200}
    elif heading_error > 0:
        # Target is to the left — turn left
        return {"left_speed": NAV_SPEED // 2, "right_speed": NAV_SPEED, "duration_ms": 150}
    else:
        # Target is to the right — turn right
        return {"left_speed": NAV_SPEED, "right_speed": NAV_SPEED // 2, "duration_ms": 150}


class NavigateToTarget(py_trees.behaviour.Behaviour):
    """
    Steers the robot toward an active waypoint set by VictimConfirmation or
    any external mission command. Returns RUNNING while en-route, FAILURE
    once arrived or when no target exists.
    """

    def __init__(self, blackboard, name: str = "NavigateToTarget"):
        super().__init__(name=name)
        self.bb = blackboard

    def update(self) -> py_trees.common.Status:
        waypoint   = self.bb.get("navigation/target_waypoint")
        robot_pose = self.bb.get("navigation/robot_pose")

        if waypoint is None:
            self.feedback_message = "No active waypoint"
            return py_trees.common.Status.FAILURE

        if robot_pose is None:
            self.feedback_message = "No pose data"
            return py_trees.common.Status.FAILURE

        target_row, target_col = waypoint
        robot_row, robot_col   = world_to_grid(robot_pose["x"], robot_pose["y"])
        dist = _cells_distance(robot_row, robot_col, target_row, target_col)

        if dist <= ARRIVAL_RADIUS_CELLS:
            # Arrived! Clear the waypoint
            self.bb.set("navigation/target_waypoint", None)
            self.bb.set("state/bt_status", "ARRIVED_AT_TARGET")
            self.bb.set("state/motor_command",
                        {"left_speed": 0, "right_speed": 0, "duration_ms": 200})
            self.feedback_message = "Arrived at waypoint"
            return py_trees.common.Status.FAILURE   # Done — fall through

        # Still navigating
        motor_cmd = _steer_toward(robot_pose, target_row, target_col)
        self.bb.set("state/motor_command", motor_cmd)
        self.bb.set("state/bt_status",
                    f"NAVIGATING_TO_TARGET [dist={dist:.1f} cells]")

        self.feedback_message = f"En-route to {waypoint}, dist={dist:.1f} cells"
        return py_trees.common.Status.RUNNING
