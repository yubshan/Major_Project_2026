"""Sequential PPO curriculum for the six deterministic house layouts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulation_brain.rl.dashboard import TrainingDashboard
from simulation_brain.rl.environment import SARSimulationEnv, mixed_house_env
from simulation_brain.rl.features import OBSERVATION_SCHEMA, OBSERVATION_SIZE
from simulation_brain.rl.reports import write_reports
from simulation_brain.scenarios import HOUSE_SCENARIOS

PRESETS = {
    "quick": {"house": 5_000, "mixed": 10_000},
    "full": {"house": 50_000, "mixed": 100_000},
}


def _dependencies():
    try:
        from stable_baselines3 import PPO
        from stable_baselines3.common.callbacks import BaseCallback
        from stable_baselines3.common.monitor import Monitor
    except ImportError as exc:
        raise RuntimeError(
            "Training requires stable-baselines3 and Gymnasium; install the project requirements"
        ) from exc
    return PPO, BaseCallback, Monitor


def validate_model_schema(model) -> None:
    actual = tuple(model.observation_space.shape)
    if actual != (OBSERVATION_SIZE,):
        raise ValueError(
            f"Checkpoint uses observation shape {actual}; expected {OBSERVATION_SCHEMA} "
            f"({OBSERVATION_SIZE},). Retrain it or resume a v2 checkpoint."
        )


def _callback(base_callback, records: list[dict], dashboard: TrainingDashboard, stage: str):
    class CurriculumCallback(base_callback):
        def _on_step(self) -> bool:
            infos = self.locals.get("infos", [])
            dones = self.locals.get("dones", [])
            for info, done in zip(infos, dones):
                if done:
                    row = dict(info)
                    row.update({
                        "stage": stage,
                        "episode": len(records) + 1,
                        "total_timesteps": int(self.model.num_timesteps),
                    })
                    records.append(row)
            if any(dones) or self.n_calls % 256 == 0:
                dashboard.update(stage, records, int(self.model.num_timesteps))
            return True
    return CurriculumCallback()


def train_curriculum(
    *,
    preset: str = "quick",
    seed: int = 7,
    dashboard_enabled: bool = False,
    resume: Path | None = None,
    output_dir: Path = Path("simulation_brain/models"),
    report_dir: Path = Path("simulation_brain/reports/latest"),
    house_timesteps: int | None = None,
    mixed_timesteps: int | None = None,
) -> Path:
    PPO, BaseCallback, Monitor = _dependencies()
    schedule = PRESETS[preset]
    house_steps = int(house_timesteps if house_timesteps is not None else schedule["house"])
    mixed_steps = int(mixed_timesteps if mixed_timesteps is not None else schedule["mixed"])
    output_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    dashboard = TrainingDashboard(dashboard_enabled)
    records: list[dict] = []

    model = None
    start_stage = 0
    if resume is not None:
        model = PPO.load(str(resume))
        validate_model_schema(model)
        resume_state = resume.with_suffix(".json")
        if resume_state.is_file():
            state = json.loads(resume_state.read_text(encoding="utf-8"))
            if state.get("schema") != OBSERVATION_SCHEMA:
                raise ValueError(
                    f"Resume metadata is not {OBSERVATION_SCHEMA}; retrain or select a v2 checkpoint"
                )
            start_stage = len(state.get("completed_stages", ()))

    stages = [(name, house_steps) for name in HOUSE_SCENARIOS] + [("mixed-layouts", mixed_steps)]
    try:
        for index, (stage, timesteps) in enumerate(stages[start_stage:], start=start_stage + 1):
            raw_env = (
                mixed_house_env(seed=seed)
                if stage == "mixed-layouts"
                else SARSimulationEnv(scenario=stage, base_seed=seed)
            )
            env = Monitor(raw_env)
            if model is None:
                model = PPO("MlpPolicy", env, verbose=1, seed=seed)
            else:
                model.set_env(env)
            callback = _callback(BaseCallback, records, dashboard, stage)
            model.learn(
                total_timesteps=timesteps,
                reset_num_timesteps=False,
                callback=callback,
                progress_bar=False,
            )
            checkpoint = output_dir / f"{index:02d}_{stage}.zip"
            model.save(str(checkpoint))
            model.save(str(output_dir / "latest.zip"))
            stage_metadata = {
                "schema": OBSERVATION_SCHEMA,
                "observation_size": OBSERVATION_SIZE,
                "preset": preset,
                "seed": seed,
                "completed_stages": [name for name, _ in stages[:index]],
                "total_timesteps": int(model.num_timesteps),
            }
            checkpoint.with_suffix(".json").write_text(
                json.dumps(stage_metadata, indent=2), encoding="utf-8"
            )
            (output_dir / "latest.json").write_text(
                json.dumps(stage_metadata, indent=2), encoding="utf-8"
            )
            env.close()

        final_path = output_dir / "house_rescue_final.zip"
        assert model is not None
        model.save(str(final_path))
        metadata = {
            "schema": OBSERVATION_SCHEMA,
            "observation_size": OBSERVATION_SIZE,
            "preset": preset,
            "seed": seed,
            "house_timesteps": house_steps,
            "mixed_timesteps": mixed_steps,
            "total_timesteps": int(model.num_timesteps),
            "stages": [stage for stage, _ in stages],
            "completed_stages": [stage for stage, _ in stages],
        }
        (output_dir / "latest.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        write_reports(records, report_dir, metadata)
        return final_path
    finally:
        dashboard.close()


def train(timesteps: int, seed: int, output: Path) -> Path:
    """Backward-compatible single-stage trainer used by older scripts."""
    PPO, _, Monitor = _dependencies()
    output.parent.mkdir(parents=True, exist_ok=True)
    env = Monitor(SARSimulationEnv(scenario="studio-apartment", base_seed=seed))
    model = PPO("MlpPolicy", env, verbose=1, seed=seed)
    model.learn(total_timesteps=timesteps)
    model.save(str(output))
    env.close()
    return output if output.suffix == ".zip" else output.with_suffix(".zip")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the house-rescue PPO curriculum")
    parser.add_argument("--preset", choices=tuple(PRESETS), default="quick")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--dashboard", action="store_true")
    parser.add_argument("--resume", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("simulation_brain/models"))
    parser.add_argument("--report-dir", type=Path, default=Path("simulation_brain/reports/latest"))
    parser.add_argument("--house-timesteps", type=int, help=argparse.SUPPRESS)
    parser.add_argument("--mixed-timesteps", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    result = train_curriculum(
        preset=args.preset,
        seed=args.seed,
        dashboard_enabled=args.dashboard,
        resume=args.resume,
        output_dir=args.output_dir,
        report_dir=args.report_dir,
        house_timesteps=args.house_timesteps,
        mixed_timesteps=args.mixed_timesteps,
    )
    print(result)


if __name__ == "__main__":
    main()
