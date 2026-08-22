"""Command-line entry point for Simulation Brain."""

import argparse

from simulation_brain.runner import run_headless, run_visual
from simulation_brain.scenarios import SCENARIO_NAMES


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Drishya SAR simulation")
    parser.add_argument("--mode", choices=("visual", "headless"), default="visual")
    parser.add_argument(
        "--scenario",
        choices=SCENARIO_NAMES,
        default="studio-apartment",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--model", help="Optional Simulation Brain PPO .zip checkpoint")
    parser.add_argument(
        "--speed", type=float, choices=(0.25, 0.5, 1.0, 2.0), default=0.5,
        help="Visual playback multiplier (default: 0.5 for presentations)",
    )
    parser.add_argument(
        "--moving-obstacles", type=int,
        help="Autonomous moving hazards (default: 2 visual, 0 headless)",
    )
    parser.add_argument(
        "--obstacle-interval", type=int, default=10,
        help="Decision ticks between moving-obstacle updates (default: 10)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    moving_obstacles = args.moving_obstacles
    if moving_obstacles is None:
        moving_obstacles = 2 if args.mode == "visual" else 0
    if args.mode == "visual":
        run_visual(
            args.scenario, args.seed, args.model, args.speed,
            moving_obstacles, args.obstacle_interval,
        )
    else:
        run_headless(
            args.scenario, args.seed, args.episodes, args.max_steps, args.model,
            moving_obstacles, args.obstacle_interval,
        )


if __name__ == "__main__":
    main()
