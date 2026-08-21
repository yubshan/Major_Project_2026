"""Train a PPO exploration policy. Stable-Baselines3 is optional at runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from simulation_brain.rl.environment import SARSimulationEnv


def train(timesteps: int, seed: int, output: Path) -> Path:
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.monitor import Monitor
    except ImportError as exc:
        raise RuntimeError(
            "Training requires stable-baselines3; install modules/decision_logic/requirements.txt"
        ) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    env = Monitor(SARSimulationEnv())
    model = PPO("MlpPolicy", env, verbose=1, seed=seed)
    model.learn(total_timesteps=timesteps)
    model.save(str(output))
    env.close()
    return output.with_suffix(".zip")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train Simulation Brain PPO exploration")
    parser.add_argument("--timesteps", type=int, default=100_000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output", type=Path, default=Path("simulation_brain/models/ppo_explore"))
    args = parser.parse_args()
    print(train(args.timesteps, args.seed, args.output))


if __name__ == "__main__":
    main()

