"""Visual replay of an untrained, deterministic, or trained direct-action episode."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from simulation_brain.rl.environment import SARSimulationEnv
from simulation_brain.rl.features import deterministic_frontier_action
from simulation_brain.rl.train_ppo import validate_model_schema
from simulation_brain.scenarios import HOUSE_SCENARIOS


def replay(scenario: str, seed: int, policy: str, model_path: Path | None, speed: float = 2.0) -> dict:
    from simulation_brain.renderer import SimulationRenderer
    from simulation_brain.visual_state import VisualSessionState

    model = None
    if model_path is not None:
        from stable_baselines3 import PPO
        model = PPO.load(str(model_path))
        validate_model_schema(model)
        policy = "ppo"

    env = SARSimulationEnv(scenario=scenario, base_seed=seed)
    obs, info = env.reset(seed=seed)
    assert env.controller is not None
    renderer = SimulationRenderer(env.controller)
    visual = VisualSessionState.from_controller(env.controller, speed=min(2.0, max(0.25, speed)))
    visual.paused = False
    rng = np.random.default_rng(seed)
    terminated = truncated = False
    running = True
    accumulator = 0.0
    try:
        while running:
            elapsed = renderer.clock.tick(env.controller.config.fps) / 1000.0
            visual.advance(elapsed)
            accumulator += elapsed
            for event in renderer.pg.event.get():
                if event.type == renderer.pg.QUIT or (
                    event.type == renderer.pg.KEYDOWN and event.key == renderer.pg.K_ESCAPE
                ):
                    running = False
            interval = 1.0 / (env.controller.config.tick_hz * visual.speed)
            if running and not (terminated or truncated) and not visual.animating and accumulator >= interval:
                if model is not None:
                    action, _ = model.predict(obs, deterministic=True)
                    action = int(action)
                elif policy == "deterministic-frontier":
                    action = deterministic_frontier_action(obs)
                else:
                    action = int(rng.integers(4))
                obs, _, terminated, truncated, info = env.step(action)
                visual.begin_transition(env.controller.robot, env.controller.heading, min(0.2, interval * 0.8))
                accumulator = 0.0
            renderer.draw(visual)
            if terminated or truncated:
                env.controller.terminated = True
    finally:
        renderer.close()
        env.close()
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay a house-rescue training episode")
    parser.add_argument("--scenario", choices=HOUSE_SCENARIOS, default="two-bedroom-house")
    parser.add_argument("--policy", choices=("random", "deterministic-frontier"), default="random")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--speed", type=float, default=2.0)
    args = parser.parse_args()
    print(replay(args.scenario, args.seed, args.policy, args.model, args.speed))


if __name__ == "__main__":
    main()
