import json

import numpy as np

from shared.coordinate_system import OCCUPIED
from simulation_brain.planning import astar
from simulation_brain.rl.environment import SARSimulationEnv, mixed_house_env
from simulation_brain.rl.features import OBSERVATION_SCHEMA, OBSERVATION_SIZE, build_observation
from simulation_brain.rl.reports import write_reports
from simulation_brain.rl.train_ppo import PRESETS, validate_model_schema
from simulation_brain.scenarios import HOUSE_SCENARIOS, create_scenario


def test_all_house_layouts_are_deterministic_and_solvable():
    assert len(HOUSE_SCENARIOS) == 6
    for name in HOUSE_SCENARIOS:
        first = create_scenario(name, 7)
        second = create_scenario(name, 7)
        assert first.room_count >= 3
        assert np.array_equal(first.ground_truth, second.ground_truth)
        assert first.victim == second.victim
        assert first.ground_truth[first.start] != OCCUPIED
        assert astar(first.ground_truth, first.start, first.victim).status == "ok"


def test_victim_relative_fields_are_masked_until_confirmation():
    env = SARSimulationEnv("studio-apartment")
    env.reset(seed=7)
    assert env.controller is not None
    hidden = build_observation(env.controller, victim_confirmed=False)
    visible = build_observation(env.controller, victim_confirmed=True)
    assert hidden.shape == (OBSERVATION_SIZE,)
    assert np.array_equal(hidden[-3:-1], np.zeros(2))
    assert not np.array_equal(visible[-3:-1], np.zeros(2))
    env.close()


def test_collision_does_not_move_robot_and_escalates_penalty():
    env = SARSimulationEnv("studio-apartment")
    env.reset(seed=7)
    assert env.controller is not None
    start = env.controller.robot
    env.controller.ground_truth[start[0], start[1] + 1] = OCCUPIED
    _, first_reward, _, _, first_info = env.step(0)
    assert env.controller.robot == start
    assert first_info["collisions"] == 1
    _, second_reward, _, _, second_info = env.step(0)
    assert env.controller.robot == start
    assert second_info["collisions"] == 2
    assert second_reward < first_reward
    env.close()


def test_identical_seed_and_actions_produce_identical_trajectory():
    actions = (0, 1, 0, 3, 2, 0)
    trajectories = []
    for _ in range(2):
        env = SARSimulationEnv("two-bedroom-house", max_steps=20)
        observation, _ = env.reset(seed=19)
        trajectory = [(observation.copy(), env.controller.robot)]
        for action in actions:
            observation, reward, terminated, truncated, info = env.step(action)
            trajectory.append((observation.copy(), env.controller.robot, reward, info["collisions"]))
            if terminated or truncated:
                break
        trajectories.append(trajectory)
        env.close()
    assert len(trajectories[0]) == len(trajectories[1])
    for left, right in zip(*trajectories):
        assert np.array_equal(left[0], right[0])
        assert left[1:] == right[1:]


def test_curriculum_order_presets_and_mixed_rotation():
    assert PRESETS["quick"] == {"house": 5_000, "mixed": 10_000}
    assert PRESETS["full"] == {"house": 50_000, "mixed": 100_000}
    env = mixed_house_env(seed=7)
    observed = []
    for _ in HOUSE_SCENARIOS:
        _, info = env.reset()
        observed.append(info["scenario"])
    assert tuple(observed) == HOUSE_SCENARIOS
    env.close()


def test_legacy_model_schema_is_rejected():
    class Space:
        shape = (2513,)

    class Model:
        observation_space = Space()

    try:
        validate_model_schema(Model())
    except ValueError as exc:
        assert OBSERVATION_SCHEMA in str(exc)
        assert "Retrain" in str(exc)
    else:
        raise AssertionError("legacy checkpoint was accepted")


def test_report_generation_is_dependency_free(tmp_path):
    records = [{
        "stage": "studio-apartment", "scenario": "studio-apartment", "seed": 7,
        "episode": 1, "total_timesteps": 20, "episode_reward": -4.0,
        "rescued": False, "collisions": 3, "steps": 20,
        "detection_step": None, "coverage_pct": 14.0,
    }, {
        "stage": "studio-apartment", "scenario": "studio-apartment", "seed": 7,
        "episode": 2, "total_timesteps": 40, "episode_reward": 110.0,
        "rescued": True, "collisions": 0, "steps": 18,
        "detection_step": 12, "coverage_pct": 22.0,
    }]
    paths = write_reports(records, tmp_path, {"schema": OBSERVATION_SCHEMA})
    assert all(path.is_file() for path in paths.values())
    assert json.loads(paths["json"].read_text())["per_house"][0]["episodes"] == 2
    assert "<svg" in paths["html"].read_text()
