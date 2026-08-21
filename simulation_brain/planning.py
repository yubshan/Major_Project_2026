"""Deterministic Dijkstra planning and frontier selection."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

import numpy as np

from shared.coordinate_system import FREE, GRID_HEIGHT, GRID_WIDTH, UNKNOWN

Cell = tuple[int, int]
NEIGHBORS: tuple[Cell, ...] = ((-1, 0), (0, -1), (0, 1), (1, 0))


@dataclass(frozen=True)
class PathResult:
    path: list[Cell]
    cost: int | None
    status: str


def _valid(cell: Cell) -> bool:
    return 0 <= cell[0] < GRID_HEIGHT and 0 <= cell[1] < GRID_WIDTH


def dijkstra(grid: np.ndarray, start: Cell, goal: Cell) -> PathResult:
    """Return the shortest four-connected path, excluding start, through known FREE cells."""
    if not (_valid(start) and _valid(goal)):
        return PathResult([], None, "out_of_bounds")
    if start == goal:
        return PathResult([], 0, "arrived")
    if grid[start] != FREE or grid[goal] != FREE:
        return PathResult([], None, "blocked_goal_or_start")

    frontier: list[tuple[int, Cell]] = [(0, start)]
    distance = {start: 0}
    previous: dict[Cell, Cell] = {}
    while frontier:
        cost, cell = heapq.heappop(frontier)
        if cost != distance[cell]:
            continue
        if cell == goal:
            break
        for dr, dc in NEIGHBORS:
            nxt = cell[0] + dr, cell[1] + dc
            if not _valid(nxt) or grid[nxt] != FREE:
                continue
            new_cost = cost + 1
            if new_cost < distance.get(nxt, 10**9):
                distance[nxt] = new_cost
                previous[nxt] = cell
                heapq.heappush(frontier, (new_cost, nxt))

    if goal not in distance:
        return PathResult([], None, "unreachable")
    path = []
    cursor = goal
    while cursor != start:
        path.append(cursor)
        cursor = previous[cursor]
    path.reverse()
    return PathResult(path, distance[goal], "ok")


def information_gain(grid: np.ndarray, cell: Cell, radius: int = 2) -> int:
    row, col = cell
    r0, r1 = max(0, row - radius), min(GRID_HEIGHT, row + radius + 1)
    c0, c1 = max(0, col - radius), min(GRID_WIDTH, col + radius + 1)
    return int(np.count_nonzero(grid[r0:r1, c0:c1] == UNKNOWN))


def reachable_frontiers(grid: np.ndarray, start: Cell) -> list[tuple[Cell, int, int]]:
    """Return reachable FREE frontier cells as (cell, distance, information gain)."""
    queue = [(start, 0)]
    seen = {start}
    result = []
    for cell, distance in queue:
        row, col = cell
        is_frontier = False
        for dr, dc in NEIGHBORS:
            nxt = row + dr, col + dc
            if not _valid(nxt):
                continue
            if grid[nxt] == UNKNOWN:
                is_frontier = True
            elif grid[nxt] == FREE and nxt not in seen:
                seen.add(nxt)
                queue.append((nxt, distance + 1))
        if is_frontier and cell != start:
            result.append((cell, distance, information_gain(grid, cell)))
    return result


def choose_frontier(grid: np.ndarray, start: Cell, sector: int | None = None) -> Cell | None:
    """Pick a frontier by distance, then information gain, optionally preferring a sector."""
    candidates = reachable_frontiers(grid, start)
    if not candidates:
        return None

    def in_sector(cell: Cell) -> bool:
        dr, dc = cell[0] - start[0], cell[1] - start[1]
        return (
            (sector == 0 and dc >= abs(dr))
            or (sector == 1 and -dr >= abs(dc))
            or (sector == 2 and -dc >= abs(dr))
            or (sector == 3 and dr >= abs(dc))
        )

    preferred = [item for item in candidates if sector is not None and in_sector(item[0])]
    pool = preferred or candidates
    return min(pool, key=lambda item: (item[1], -item[2], item[0]))[0]


def nearest_reachable_neighbor(grid: np.ndarray, start: Cell, goal: Cell) -> Cell | None:
    candidates = []
    for dr, dc in NEIGHBORS:
        cell = goal[0] + dr, goal[1] + dc
        result = dijkstra(grid, start, cell) if _valid(cell) else PathResult([], None, "invalid")
        if result.cost is not None:
            candidates.append((result.cost, cell))
    return min(candidates)[1] if candidates else None

