import numpy as np

from shared.coordinate_system import FREE, OCCUPIED, UNKNOWN
from simulation_brain.planning import choose_frontier, dijkstra


def test_dijkstra_shortest_path_avoids_obstacle():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    grid[25, 26] = OCCUPIED
    result = dijkstra(grid, (25, 25), (25, 27))
    assert result.status == "ok"
    assert result.cost == 4
    assert (25, 26) not in result.path


def test_dijkstra_is_deterministic_and_excludes_start():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    first = dijkstra(grid, (10, 10), (12, 12))
    second = dijkstra(grid, (10, 10), (12, 12))
    assert first == second
    assert first.path[0] != (10, 10)


def test_dijkstra_reports_invalid_and_unreachable_goals():
    grid = np.full((50, 50), FREE, dtype=np.int8)
    grid[9:12, 9:12] = OCCUPIED
    grid[10, 10] = FREE
    assert dijkstra(grid, (0, 0), (50, 1)).status == "out_of_bounds"
    assert dijkstra(grid, (0, 0), (10, 10)).status == "unreachable"


def test_frontier_is_reachable_known_free_cell():
    grid = np.full((50, 50), UNKNOWN, dtype=np.int8)
    grid[25, 25:29] = FREE
    target = choose_frontier(grid, (25, 25), sector=0)
    assert target in {(25, 26), (25, 27), (25, 28)}
    assert dijkstra(grid, (25, 25), target).status == "ok"
