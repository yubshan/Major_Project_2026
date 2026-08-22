"""Command-line entry point for Simulation Brain."""

import argparse

from simulation_brain.runner import run_headless, run_visual


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Project Drishya SAR simulation")
    parser.add_argument("--mode", choices=("visual", "headless"), default="visual")
    parser.add_argument(
        "--scenario",
        choices=("open-room", "maze", "corridor", "blocked-route", "unreachable-target", "random"),
        default="random",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--episodes", type=int, default=1)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--model", help="Optional Simulation Brain PPO .zip checkpoint")
    parser.add_argument(
        "--speed", type=float, choices=(0.25, 0.5, 1.0, 2.0), default=0.5,
        help="Visual playback multiplier (default: 0.5 for presentations)",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if args.mode == "visual":
        run_visual(args.scenario, args.seed, args.model, args.speed)
    else:
        run_headless(args.scenario, args.seed, args.episodes, args.max_steps, args.model)


if __name__ == "__main__":
    main()
