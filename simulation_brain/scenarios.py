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


def create_scenario(name: str = "random", seed: int = 7) -> Scenario:
    """Create a deterministic scenario; normal scenarios always have a reachable victim."""
    rng = np.random.default_rng(seed)
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
        raise ValueError(
            f"Unknown scenario {name!r}; choose open-room, maze, corridor, "
            "blocked-route, unreachable-target, or random"
        )

    _clear_start(grid)
    return Scenario(name, grid, START, _choose_victim(grid, rng))

