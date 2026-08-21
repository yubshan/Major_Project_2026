import numpy as np

from simulation_brain.rl.environment import SARSimulationEnv


def test_environment_observation_and_step_contract():
    env = SARSimulationEnv(scenario="open-room", max_steps=20)
    observation, info = env.reset(seed=5)
    assert env.observation_space.contains(observation)
    assert observation.shape == (2513,)
    next_observation, reward, terminated, truncated, next_info = env.step(0)
    assert env.observation_space.contains(next_observation)
    assert isinstance(reward, float)
    assert isinstance(terminated, bool)
    assert isinstance(truncated, bool)
    assert "coverage_pct" in next_info
    env.close()


def test_observation_does_not_include_ground_truth_or_victim_coordinates():
    env = SARSimulationEnv(scenario="open-room")
    observation, _ = env.reset(seed=8)
    assert observation.size == 2500 + 13
    assert np.all((observation >= 0.0) & (observation <= 1.0))
    env.close()

