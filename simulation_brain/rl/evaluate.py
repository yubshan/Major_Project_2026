"""Evaluate random, deterministic-frontier, and PPO policies on identical houses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from simulation_brain.rl.environment import SARSimulationEnv
from simulation_brain.rl.features import deterministic_frontier_action
from simulation_brain.rl.reports import write_reports
from simulation_brain.rl.train_ppo import validate_model_schema
from simulation_brain.scenarios import HOUSE_SCENARIOS


def _load_model(model_path: Path | None):
    if model_path is None:
        return None
    try:
        from stable_baselines3 import PPO
    except ImportError as exc:
        raise RuntimeError("PPO evaluation requires stable-baselines3") from exc
    model = PPO.load(str(model_path))
    validate_model_schema(model)
    return model


def evaluate_suite(
    model_path: Path | None,
    episodes_per_scenario: int,
    seed: int,
    *,
    scenarios: tuple[str, ...] = HOUSE_SCENARIOS,
) -> list[dict]:
    model = _load_model(model_path)
    policies = ("random", "deterministic-frontier") + (("ppo",) if model is not None else ())
    results: list[dict] = []
    for scenario in scenarios:
        for split, seed_offset in (("training", 0), ("unseen", 10_000)):
            for policy in policies:
                for episode in range(episodes_per_scenario):
                    episode_seed = seed + seed_offset + episode
                    rng = np.random.default_rng(episode_seed)
                    env = SARSimulationEnv(scenario=scenario, base_seed=episode_seed)
                    obs, _ = env.reset(seed=episode_seed)
                    terminated = truncated = False
                    total_reward = 0.0
                    info = {}
                    while not (terminated or truncated):
                        if policy == "ppo":
                            action, _ = model.predict(obs, deterministic=True)
                            action = int(action)
                        elif policy == "deterministic-frontier":
                            action = deterministic_frontier_action(obs)
                        else:
                            action = int(rng.integers(4))
                        obs, reward, terminated, truncated, info = env.step(action)
                        total_reward += reward
                    row = dict(info)
                    row.update({
                        "stage": f"evaluation-{split}",
                        "split": split,
                        "policy": policy,
                        "episode": episode + 1,
                        "seed": episode_seed,
                        "episode_reward": total_reward,
                        "total_timesteps": row.get("steps", 0),
                    })
                    results.append(row)
                    env.close()
    return results


def evaluate(model_path: Path | None, episodes: int, seed: int) -> list[dict]:
    """Backward-compatible evaluation over random layouts."""
    return evaluate_suite(model_path, episodes, seed, scenarios=("random",))


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate house-rescue policies")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--suite", choices=("houses",), default="houses")
    parser.add_argument("--episodes-per-scenario", type=int, default=20)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--output-dir", type=Path, default=Path("simulation_brain/reports/evaluation"))
    args = parser.parse_args()
    results = evaluate_suite(args.model, args.episodes_per_scenario, args.seed)
    paths = write_reports(results, args.output_dir, {
        "kind": "policy-evaluation",
        "model": str(args.model) if args.model else None,
        "seed": args.seed,
    })
    print(json.dumps({"episodes": len(results), "reports": {k: str(v) for k, v in paths.items()}}, indent=2))


if __name__ == "__main__":
    main()
