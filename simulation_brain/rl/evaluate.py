"""Compare PPO and deterministic sector selection on identical seeds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from simulation_brain.rl.environment import SARSimulationEnv


def evaluate(model_path: Path | None, episodes: int, seed: int) -> list[dict]:
    model = None
    if model_path is not None:
        try:
            from stable_baselines3 import PPO
        except ImportError as exc:
            raise RuntimeError("PPO evaluation requires stable-baselines3") from exc
        model = PPO.load(str(model_path))

    results = []
    for episode in range(episodes):
        env = SARSimulationEnv()
        obs, info = env.reset(seed=seed + episode)
        terminated = truncated = False
        while not (terminated or truncated):
            if model is not None:
                action, _ = model.predict(obs, deterministic=True)
                action = int(action)
            else:
                # Final four observation values are normalized frontier counts.
                action = int(np.argmax(obs[-4:]))
            obs, _, terminated, truncated, info = env.step(action)
        info.update({
            "episode": episode,
            "seed": seed + episode,
            "policy": "ppo" if model is not None else "deterministic",
        })
        results.append(info)
        env.close()
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate exploration policies")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    print(json.dumps(evaluate(args.model, args.episodes, args.seed), indent=2))


if __name__ == "__main__":
    main()
