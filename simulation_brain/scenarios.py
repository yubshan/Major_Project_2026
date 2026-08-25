"""Seeded ground-truth maps used by the simulator and RL environment."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from shared.coordinate_system import (
    FREE,
    GRID_CENTER_X,
    GRID_CENTER_Y,
    GRID_HEIGHT,
    GRID_WIDTH,
    OCCUPIED,
)

Cell = tuple[int, int]
START: Cell = (GRID_CENTER_Y, GRID_CENTER_X)


@dataclass(frozen=True)
class Scenario:
    name: str
    ground_truth: np.ndarray
    start: Cell
    victim: Cell
    room_count: int = 1
    room_labels: tuple[str, ...] = ()


HOUSE_SCENARIOS = (
    "studio-apartment",
    "two-bedroom-house",
    "office-suite",
    "clinic-ward",
    "warehouse",
    "collapsed-house",
)
ABSTRACT_SCENARIOS = (
    "open-room", "corridor", "maze", "blocked-route", "unreachable-target", "random",
)
SCENARIO_NAMES = HOUSE_SCENARIOS + ABSTRACT_SCENARIOS

# Renderer-only semantic anchors. They make the fixed structures readable during
# a defense without publishing architectural labels to the Blackboard or policy.
HOUSE_ROOM_ANNOTATIONS: dict[str, tuple[tuple[str, Cell], ...]] = {
    "studio-apartment": (
        ("LIVING / SLEEPING", (12, 17)), ("KITCHEN", (40, 23)), ("BATH", (10, 41)),
    ),
    "two-bedroom-house": (
        ("BEDROOM 1", (11, 8)), ("BEDROOM 2", (11, 26)), ("BATH", (10, 42)),
        ("LIVING", (34, 24)), ("KITCHEN", (40, 43)), ("HALL", (21, 25)),
    ),
    "office-suite": (
        ("LOBBY", (7, 20)), ("OFFICES", (8, 43)), ("CUBICLES", (26, 26)),
        ("MEETING", (42, 25)), ("OFFICE", (42, 43)),
    ),
    "clinic-ward": (
        ("RECEPTION", (8, 8)), ("TREATMENT", (8, 23)), ("STORAGE", (8, 41)),
        ("WARD", (29, 25)), ("PASSAGE", (43, 25)),
    ),
    "warehouse": (
        ("LOADING", (6, 25)), ("SHELVING AISLES", (27, 25)),
        ("STORAGE", (44, 25)),
    ),
    "collapsed-house": (
        ("DAMAGED ROOM", (8, 8)), ("RUBBLE", (9, 27)),
        ("LIVING", (27, 27)), ("DETOUR", (44, 27)),
    ),
}


def _empty_room() -> np.ndarray:
    grid = np.full((GRID_HEIGHT, GRID_WIDTH), FREE, dtype=np.int8)
    grid[0, :] = OCCUPIED
    grid[-1, :] = OCCUPIED
    grid[:, 0] = OCCUPIED
    grid[:, -1] = OCCUPIED
    return grid


def _reachable(grid: np.ndarray, start: Cell) -> set[Cell]:
    seen = {start}
    queue = deque([start])
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (0, -1), (1, 0), (0, 1)):
            nxt = row + dr, col + dc
            if (
                0 <= nxt[0] < GRID_HEIGHT
                and 0 <= nxt[1] < GRID_WIDTH
                and grid[nxt] == FREE
                and nxt not in seen
            ):
                seen.add(nxt)
                queue.append(nxt)
    return seen


def _choose_victim(grid: np.ndarray, rng: np.random.Generator) -> Cell:
    candidates = [
        cell
        for cell in _reachable(grid, START)
        if abs(cell[0] - START[0]) + abs(cell[1] - START[1]) >= 14
    ]
    if not candidates:
        candidates = list(_reachable(grid, START) - {START})
    candidates.sort()
    return candidates[int(rng.integers(len(candidates)))]


def _clear_start(grid: np.ndarray) -> None:
    row, col = START
    grid[row - 2 : row + 3, col - 2 : col + 3] = FREE


def _horizontal_wall(grid: np.ndarray, row: int, left: int, right: int, *doors: int) -> None:
    grid[row, left : right + 1] = OCCUPIED
    for door in doors:
        grid[row, door : door + 2] = FREE


def _vertical_wall(grid: np.ndarray, col: int, top: int, bottom: int, *doors: int) -> None:
    grid[top : bottom + 1, col] = OCCUPIED
    for door in doors:
        grid[door : door + 2, col] = FREE


def _furniture(grid: np.ndarray, top: int, left: int, height: int, width: int) -> None:
    grid[top : top + height, left : left + width] = OCCUPIED


def _house_layout(name: str) -> tuple[np.ndarray, tuple[Cell, ...], tuple[str, ...]]:
    """Return fixed architecture, victim candidates, and human-readable room labels."""
    grid = _empty_room()
    candidates: tuple[Cell, ...]
    labels: tuple[str, ...]

    if name == "studio-apartment":
        _vertical_wall(grid, 34, 1, 20, 14)
        _horizontal_wall(grid, 20, 34, 48, 41)
        _furniture(grid, 6, 6, 3, 7)       # bed
        _furniture(grid, 37, 6, 3, 10)     # kitchen counter
        _furniture(grid, 29, 34, 4, 2)     # sofa
        _furniture(grid, 7, 40, 3, 4)      # bathroom fixture
        candidates = ((8, 18), (10, 42), (38, 20), (38, 40))
        labels = ("living/sleeping area", "kitchen", "bathroom")
    elif name == "two-bedroom-house":
        _horizontal_wall(grid, 18, 1, 48, 9, 27, 40)
        _vertical_wall(grid, 18, 1, 18, 9)
        _vertical_wall(grid, 34, 1, 18, 9)
        _vertical_wall(grid, 12, 18, 48, 27)
        _vertical_wall(grid, 37, 18, 48, 34)
        _furniture(grid, 5, 4, 4, 7)
        _furniture(grid, 5, 23, 4, 7)
        _furniture(grid, 35, 3, 3, 7)
        _furniture(grid, 36, 42, 5, 3)
        candidates = ((11, 7), (11, 25), (10, 42), (35, 20), (39, 42))
        labels = ("bedroom one", "bedroom two", "bathroom", "living room", "kitchen", "hallway")
    elif name == "office-suite":
        _horizontal_wall(grid, 12, 1, 38, 8, 24)
        _vertical_wall(grid, 38, 1, 35, 7, 25)
        _horizontal_wall(grid, 35, 12, 48, 20, 43)
        _vertical_wall(grid, 12, 12, 48, 23, 40)
        for row in (18, 25):
            for col in (18, 25, 32):
                _furniture(grid, row, col, 2, 3)
        _furniture(grid, 4, 43, 5, 2)
        _furniture(grid, 40, 20, 3, 8)
        candidates = ((6, 8), (7, 44), (22, 22), (29, 30), (42, 24), (42, 43))
        labels = ("lobby", "private offices", "cubicles", "meeting room", "intersecting corridors")
    elif name == "clinic-ward":
        _horizontal_wall(grid, 14, 1, 48, 7, 20, 36, 45)
        _vertical_wall(grid, 15, 1, 14, 7)
        _vertical_wall(grid, 31, 1, 14, 7)
        _vertical_wall(grid, 10, 14, 48, 25, 41)
        _vertical_wall(grid, 39, 14, 48, 25, 41)
        for row in (20, 29, 38):
            for col in (17, 29):
                _furniture(grid, row, col, 2, 5)  # ward beds
        _furniture(grid, 4, 41, 5, 4)
        candidates = ((8, 7), (8, 23), (8, 41), (24, 20), (34, 31), (42, 44))
        labels = ("reception", "treatment rooms", "ward", "storage", "constrained passages")
    elif name == "warehouse":
        _horizontal_wall(grid, 10, 1, 48, 16, 32, 44)
        for col in (8, 16, 24, 32, 40):
            for top in (15, 30):
                _furniture(grid, top, col, 10, 3)
        _furniture(grid, 4, 4, 3, 8)
        _furniture(grid, 4, 36, 3, 8)
        candidates = ((6, 20), (19, 13), (27, 37), (42, 5), (43, 28), (42, 45))
        labels = ("loading bay", "shelving aisles", "bulk storage", "alternative routes")
    elif name == "collapsed-house":
        _horizontal_wall(grid, 16, 1, 48, 8, 26, 42)
        _vertical_wall(grid, 17, 1, 40, 8, 25)
        _vertical_wall(grid, 36, 16, 48, 24, 41)
        _horizontal_wall(grid, 39, 1, 36, 10, 28)
        # Irregular rubble clusters leave deliberate detours through the structure.
        for top, left, height, width in (
            (6, 25, 3, 5), (18, 5, 4, 4), (20, 29, 3, 4),
            (31, 13, 3, 5), (42, 22, 3, 4), (31, 42, 4, 3),
        ):
            _furniture(grid, top, left, height, width)
        candidates = ((7, 7), (8, 42), (23, 11), (29, 29), (44, 8), (44, 43))
        labels = ("damaged bedrooms", "living area", "rubble zones", "blocked passages", "detours")
    else:
        raise ValueError(name)

    _clear_start(grid)
    # Furniture must never occupy the shared robot start clearance.
    reachable = _reachable(grid, START)
    valid = tuple(cell for cell in candidates if cell in reachable and grid[cell] == FREE)
    if not valid:
        raise RuntimeError(f"House scenario {name!r} has no reachable victim candidate")
    return grid, valid, labels


def create_scenario(name: str = "random", seed: int = 7) -> Scenario:
    """Create a deterministic scenario; normal scenarios always have a reachable victim."""
    rng = np.random.default_rng(seed)
    if name in HOUSE_SCENARIOS:
        grid, candidates, labels = _house_layout(name)
        victim = candidates[int(rng.integers(len(candidates)))]
        return Scenario(name, grid, START, victim, len(labels), labels)

    grid = _empty_room()

    if name == "open-room":
        for row, col in ((12, 15), (12, 16), (35, 33), (36, 33), (20, 38)):
            grid[row, col] = OCCUPIED
    elif name == "corridor":
        grid[8:43, 18] = OCCUPIED
        grid[8:43, 32] = OCCUPIED
        grid[24:28, 18] = FREE
        grid[15:18, 32] = FREE
    elif name == "maze":
        for col in range(6, 45, 6):
            grid[4:46, col] = OCCUPIED
            gap = 7 + ((col * 3 + seed) % 32)
            grid[gap : gap + 4, col] = FREE
    elif name == "blocked-route":
        grid[10:41, 30] = OCCUPIED
        grid[35:39, 30] = FREE
    elif name == "unreachable-target":
        victim = (8, 8)
        grid[7:10, 7] = OCCUPIED
        grid[7:10, 9] = OCCUPIED
        grid[7, 7:10] = OCCUPIED
        grid[9, 7:10] = OCCUPIED
        _clear_start(grid)
        return Scenario(name, grid, START, victim)
    elif name == "random":
        mask = rng.random((GRID_HEIGHT, GRID_WIDTH)) < 0.12
        grid[mask] = OCCUPIED
        # Carve guaranteed cross-shaped connectivity, then retain random branches.
        grid[START[0], 1:-1] = FREE
        grid[1:-1, START[1]] = FREE
    else:
        raise ValueError(f"Unknown scenario {name!r}; choose one of {', '.join(SCENARIO_NAMES)}")

    _clear_start(grid)
    return Scenario(name, grid, START, _choose_victim(grid, rng))
