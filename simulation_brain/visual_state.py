"""Renderer-only state for animation and presentation controls."""

from __future__ import annotations

from dataclasses import dataclass, field

Cell = tuple[int, int]


@dataclass(frozen=True)
class VisualPose:
    row: float
    col: float
    heading: float


def _heading_delta(start: float, end: float) -> float:
    """Return the shortest signed turn from start to end in degrees."""
    return (end - start + 180.0) % 360.0 - 180.0


@dataclass
class VisualSessionState:
    """UI state kept separate from the deterministic simulation controller."""

    previous_pose: VisualPose
    current_pose: VisualPose
    speed: float = 0.5
    view_mode: str = "perception"
    show_sensors: bool = True
    show_path: bool = True
    edit_obstacles: bool = False
    paused: bool = False
    transition_progress: float = 1.0
    transition_duration: float = 0.1
    visited: set[Cell] = field(default_factory=set)
    notification: str = ""
    notification_seconds: float = 0.0
    last_edited_cell: Cell | None = None
    last_edit_occupied: bool | None = None
    presentation_mode: bool = False
    show_intro: bool = False
    show_guide: bool = False

    @classmethod
    def from_controller(
        cls, controller, speed: float = 0.5, presentation_mode: bool = False,
    ) -> "VisualSessionState":
        pose = VisualPose(float(controller.robot[0]), float(controller.robot[1]), float(controller.heading))
        return cls(
            pose, pose, speed=speed, visited={controller.robot},
            paused=presentation_mode, presentation_mode=presentation_mode,
            show_intro=presentation_mode,
        )

    @property
    def animating(self) -> bool:
        return self.transition_progress < 1.0

    def begin_transition(self, robot: Cell, heading: int, duration: float) -> None:
        self.previous_pose = self.interpolated_pose()
        self.current_pose = VisualPose(float(robot[0]), float(robot[1]), float(heading))
        self.transition_progress = 0.0
        self.transition_duration = max(0.001, float(duration))
        self.visited.add(robot)

    def advance(self, elapsed_seconds: float) -> None:
        if self.animating:
            self.transition_progress = min(
                1.0,
                self.transition_progress + max(0.0, elapsed_seconds) / self.transition_duration,
            )
        self.notification_seconds = max(0.0, self.notification_seconds - max(0.0, elapsed_seconds))
        if self.notification_seconds == 0.0:
            self.notification = ""

    def interpolated_pose(self) -> VisualPose:
        # Smoothstep avoids a mechanical start/stop without changing simulation state.
        t = self.transition_progress
        smooth = t * t * (3.0 - 2.0 * t)
        return VisualPose(
            self.previous_pose.row + (self.current_pose.row - self.previous_pose.row) * smooth,
            self.previous_pose.col + (self.current_pose.col - self.previous_pose.col) * smooth,
            (self.previous_pose.heading + _heading_delta(
                self.previous_pose.heading, self.current_pose.heading
            ) * smooth) % 360.0,
        )

    def reset_for(self, controller) -> None:
        pose = VisualPose(float(controller.robot[0]), float(controller.robot[1]), float(controller.heading))
        self.previous_pose = pose
        self.current_pose = pose
        self.transition_progress = 1.0
        self.visited = {controller.robot}
        self.paused = self.presentation_mode
        self.show_intro = self.presentation_mode
        self.show_guide = False
        self.notification = "Scenario reset with the same seed."
        self.notification_seconds = 2.5
        self.last_edited_cell = None
        self.last_edit_occupied = None

    def toggle_view(self) -> None:
        self.view_mode = "truth" if self.view_mode == "perception" else "perception"

    def adjust_speed(self, direction: int) -> None:
        speeds = (0.25, 0.5, 1.0, 2.0)
        nearest = min(range(len(speeds)), key=lambda index: abs(speeds[index] - self.speed))
        self.speed = speeds[max(0, min(len(speeds) - 1, nearest + direction))]

    def notify_map_edit(self, result) -> None:
        messages = {
            "dynamic_obstacle_added": f"Obstacle added at {result.cell}; Dijkstra replanned.",
            "dynamic_obstacle_removed": f"Obstacle removed at {result.cell}; Dijkstra replanned.",
            "robot_cell_protected": "Cannot place an obstacle on the robot.",
            "victim_cell_protected": "Cannot place an obstacle on the victim.",
            "boundary_protected": "Boundary walls are protected.",
            "no_change": "That cell already has the requested state.",
        }
        self.notification = messages.get(result.reason, f"Map edit rejected: {result.reason}.")
        self.notification_seconds = 3.0
        if result.accepted:
            self.last_edited_cell = result.cell
            self.last_edit_occupied = result.occupied
