"""Configuration shared by the visual and headless simulations."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SimulationConfig:
    tick_hz: int = 10
    max_steps: int = 750
    sensor_range_cells: int = 8
    victim_detection_range_cells: int = 10
    victim_confirmation_radius_cells: int = 1
    victim_confirm_threshold: float = 0.85
    obstacle_density: float = 0.12
    cell_pixels: int = 12
    dashboard_width: int = 420
    fps: int = 30

