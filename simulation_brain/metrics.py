"""Episode metrics published to the dashboard and headless reports."""

from dataclasses import asdict, dataclass
import time


@dataclass
class EpisodeMetrics:
    steps: int = 0
    explored_cells: int = 0
    coverage_pct: float = 0.0
    replans: int = 0
    collisions: int = 0
    unsafe_proximity_count: int = 0
    victim_detections: int = 0
    rescued: bool = False
    termination_reason: str = "running"
    policy_source: str = "heuristic"
    started_at: float = 0.0

    def start(self) -> None:
        self.started_at = time.perf_counter()

    def to_dict(self) -> dict:
        data = asdict(self)
        data["elapsed_seconds"] = max(0.0, time.perf_counter() - self.started_at)
        data.pop("started_at")
        return data
