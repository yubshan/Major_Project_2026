import numpy as np

from modules.decision_logic.contracts import PATH_STATUS, PLANNED_PATH
from shared.coordinate_system import FREE, OCCUPIED
from simulation_brain.controller import SimulationController


def test_seeded_headless_runs_are_reproducible():
    first = SimulationController("open-room", seed=4)
    second = SimulationController("open-room", seed=4)
    for _ in range(40):
        first.step()
        second.step()
    assert first.robot == second.robot
    assert first.scenario.victim == second.scenario.victim
    assert np.array_equal(first.occupancy.data, second.occupancy.data)
    assert first.metrics.steps == second.metrics.steps


def test_discovered_obstacle_invalidates_and_replans_path():
    controller = SimulationController("open-room", seed=3)
    for _ in range(20):
        controller.step()
        path = controller.blackboard.get(PLANNED_PATH, [])
        if len(path) >= 2:
            break
    assert len(path) >= 2
    blocked = tuple(path[0])
    controller.occupancy.data[blocked] = OCCUPIED
    controller._last_plan_signature = None
    controller._plan("new_obstacle")
    assert blocked not in controller.blackboard.get(PLANNED_PATH, [])
    assert controller.blackboard.get(PATH_STATUS)["replan_reason"] == "path_blocked"


def test_end_to_end_robot_rescues_victim_without_collision():
    controller = SimulationController("open-room", seed=7)
    result = controller.run(max_steps=500)
    assert result["rescued"] is True
    assert result["termination_reason"] == "victim_rescued"
    assert result["collisions"] == 0
    assert controller.blackboard.get("decision/trace")


def test_missing_ppo_checkpoint_falls_back_safely():
    controller = SimulationController("open-room", seed=7, model_path="missing-model.zip")
    assert controller._policy is None
    assert controller.policy_load_error
    controller.step()
    assert controller.metrics.policy_source == "heuristic"


def test_known_enclosed_victim_terminates_safely():
    controller = SimulationController("unreachable-target", seed=7)
    result = controller.run(max_steps=750)
    assert result["rescued"] is False
    assert result["termination_reason"] == "victim_unreachable"
    assert result["collisions"] == 0


def test_dynamic_obstacle_replans_around_edited_path_cell():
    controller = SimulationController("open-room", seed=3)
    for _ in range(20):
        controller.step()
        path = controller.blackboard.get(PLANNED_PATH, [])
        if len(path) >= 2:
            break
    assert len(path) >= 2
    blocked = tuple(path[0])
    result = controller.set_dynamic_obstacle(blocked, True)
    assert result.accepted is True
    assert controller.ground_truth[blocked] == OCCUPIED
    assert controller.occupancy.data[blocked] == OCCUPIED
    assert blocked not in controller.blackboard.get(PLANNED_PATH, [])
    assert controller.metrics.dynamic_obstacle_changes == 1
    assert controller.blackboard.get(PATH_STATUS)["replan_reason"] == "path_blocked"
    final = controller.run(max_steps=500)
    assert final["rescued"] is True
    assert final["collisions"] == 0


def test_dynamic_obstacle_can_be_removed_again():
    controller = SimulationController("open-room", seed=3)
    cell = (20, 20)
    added = controller.set_dynamic_obstacle(cell, True)
    removed = controller.set_dynamic_obstacle(cell, False)
    assert added.accepted and removed.accepted
    assert controller.ground_truth[cell] == FREE
    assert controller.occupancy.data[cell] == FREE
    assert controller.metrics.dynamic_obstacle_changes == 2


def test_dynamic_obstacle_protects_robot_victim_and_boundaries():
    controller = SimulationController("open-room", seed=3)
    assert controller.set_dynamic_obstacle(controller.robot, True).reason == "robot_cell_protected"
    assert controller.set_dynamic_obstacle(controller.scenario.victim, True).reason == "victim_cell_protected"
    assert controller.set_dynamic_obstacle((0, 10), False).reason == "boundary_protected"
    assert controller.toggle_dynamic_obstacle((99, 99)).reason == "out_of_bounds"
    assert controller.metrics.dynamic_obstacle_changes == 0
