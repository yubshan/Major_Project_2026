import numpy as np

from shared.coordinate_system import FREE, OCCUPIED, UNKNOWN
from simulation_brain.planning import astar, choose_frontier


def test_astar_shortest_path_avoids_obstacle():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    grid[25, 26] = OCCUPIED
    result = astar(grid, (25, 25), (25, 27))
    assert result.status == "ok"
    assert result.cost == 4
    assert (25, 26) not in result.path


def test_astar_is_deterministic_and_excludes_start():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    first = astar(grid, (10, 10), (12, 12))
    second = astar(grid, (10, 10), (12, 12))
    assert first == second
    assert first.path[0] != (10, 10)
    cells = [(10, 10), *first.path]
    assert all(
        abs(current[0] - previous[0]) + abs(current[1] - previous[1]) == 1
        for previous, current in zip(cells, cells[1:])
    )


def test_astar_reports_invalid_and_unreachable_goals():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    grid[9:12, 9:12] = OCCUPIED
    grid[10, 10] = FREE
    assert astar(grid, (0, 0), (50, 1)).status == "out_of_bounds"
    assert astar(grid, (0, 0), (10, 10)).status == "unreachable"


def test_frontier_is_reachable_known_free_cell():
    grid = np.full((50, 50), UNKNOWN, dtype=np.int8)
    grid[25, 25:29] = FREE
    target = choose_frontier(grid, (25, 25), sector=0)
    assert target in {(25, 26), (25, 27), (25, 28)}
    assert astar(grid, (25, 25), target).status == "ok"


def test_astar_manhattan_cost_and_known_free_only():
    grid = np.full((50, 50), UNKNOWN, dtype=np.int8)
    grid[20, 20:26] = FREE
    result = astar(grid, (20, 20), (20, 25))
    assert result.status == "ok"
    assert result.cost == 5
    assert result.path == [(20, col) for col in range(21, 26)]
    assert all(grid[cell] == FREE for cell in result.path)


def test_astar_rejects_unknown_and_blocked_goals():
    grid = np.full((50, 50), UNKNOWN, dtype=np.int8)
    grid[25, 25] = FREE
    assert astar(grid, (25, 25), (25, 26)).status == "blocked_goal_or_start"
    grid[25, 26] = OCCUPIED
    assert astar(grid, (25, 25), (25, 26)).status == "blocked_goal_or_start"
