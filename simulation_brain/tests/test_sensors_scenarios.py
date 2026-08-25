import numpy as np

from modules.navigation.occupancy_grid import OccupancyGrid
from shared.coordinate_system import FREE, OCCUPIED, UNKNOWN
from simulation_brain.planning import dijkstra
from simulation_brain.scenarios import HOUSE_SCENARIOS, create_scenario
from simulation_brain.sensors import apply_observation, sense


def test_no_hit_sensor_does_not_create_false_obstacle():
    truth = np.full((50, 50), FREE, dtype=np.int8)
    packet = sense(truth, (25, 25), 0, 4, 123)
    grid = OccupancyGrid()
    apply_observation(grid, packet, (25, 25))
    assert packet["hits"]["us_front"] is False
    assert grid.data[25, 29] == FREE
    assert not np.any(grid.data == OCCUPIED)


def test_hit_sensor_marks_endpoint_occupied():
    truth = np.full((50, 50), FREE, dtype=np.int8)
    truth[25, 28] = OCCUPIED
    packet = sense(truth, (25, 25), 0, 6, 123)
    grid = OccupancyGrid()
    apply_observation(grid, packet, (25, 25))
    assert packet["hits"]["us_front"] is True
    assert grid.data[25, 27] == FREE
    assert grid.data[25, 28] == OCCUPIED


def test_normal_scenarios_have_reachable_victims():
    for name in ("open-room", "maze", "corridor", "blocked-route", "random") + HOUSE_SCENARIOS:
        scenario = create_scenario(name, seed=11)
        result = dijkstra(scenario.ground_truth, scenario.start, scenario.victim)
        assert result.status == "ok", name


def test_unreachable_fixture_is_intentionally_unreachable():
    scenario = create_scenario("unreachable-target", seed=1)
    assert dijkstra(scenario.ground_truth, scenario.start, scenario.victim).status == "unreachable"
