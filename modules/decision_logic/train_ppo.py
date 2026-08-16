# modules/decision_logic/train_ppo.py
#
# PPO Training Script — Project Drishya, Search-and-Rescue Exploration
#
# Trains a PPO policy on SARExploreEnv using Stable-Baselines3.
# The trained model is saved to models/ppo_sar_explore.zip and is loaded
# automatically by the RLExplore behavior tree node at runtime.
#
# Run:
#   python modules/decision_logic/train_ppo.py [--steps N] [--eval]
#
# Quick demo (50k steps, ~2-3 min on CPU):
#   python modules/decision_logic/train_ppo.py --steps 50000
#
# Full training (500k steps, recommended before hardware deployment):
#   python modules/decision_logic/train_ppo.py --steps 500000

import argparse
import os
import sys
import time

# ---- make sure project root is in path ----
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import numpy as np

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import BaseCallback, EvalCallback
from stable_baselines3.common.monitor import Monitor
from gymnasium.wrappers import TimeLimit

from modules.decision_logic.rl_env.sar_explore_env import SARExploreEnv, MAX_STEPS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR    = os.path.join(_SCRIPT_DIR, "models")
MODEL_PATH   = os.path.join(MODEL_DIR, "ppo_sar_explore")
LOG_DIR      = os.path.join(_SCRIPT_DIR, "logs", "ppo")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(LOG_DIR,   exist_ok=True)


# ---------------------------------------------------------------------------
# Progress callback — prints a live training summary every N steps
# ---------------------------------------------------------------------------
class TrainingProgressCallback(BaseCallback):
    """
    Prints exploration %, mean reward, and estimated time remaining
    every `print_freq` steps so you can monitor training in the terminal.
    """

    def __init__(self, total_steps: int, print_freq: int = 5000, verbose: int = 1):
        super().__init__(verbose)
        self.total_steps  = total_steps
        self.print_freq   = print_freq
        self._start_time  = None
        self._ep_rewards  = []

    def _on_training_start(self) -> None:
        self._start_time = time.time()
        print("\n" + "═" * 70)
        print("  Project Drishya — PPO Training  |  SARExploreEnv")
        print("═" * 70)
        print(f"  Total steps  : {self.total_steps:,}")
        print(f"  Model output : {MODEL_PATH}.zip")
        print("═" * 70 + "\n")

    def _on_step(self) -> bool:
        # Collect episode rewards from the Monitor wrapper
        infos = self.locals.get("infos", [])
        for info in infos:
            if "episode" in info:
                self._ep_rewards.append(info["episode"]["r"])

        if self.n_calls % self.print_freq == 0:
            elapsed    = time.time() - self._start_time
            progress   = self.n_calls / self.total_steps
            eta_s      = (elapsed / max(progress, 1e-9)) * (1 - progress)

            mean_rew   = np.mean(self._ep_rewards[-20:]) if self._ep_rewards else float("nan")
            self._ep_rewards = self._ep_rewards[-100:]   # keep last 100

            bar_len  = 30
            filled   = int(bar_len * progress)
            bar      = "█" * filled + "░" * (bar_len - filled)

            print(
                f"  [{bar}] {100*progress:5.1f}%  "
                f"step={self.n_calls:>7,}  "
                f"mean_ep_rew={mean_rew:>7.1f}  "
                f"ETA={eta_s/60:.1f}min"
            )

        return True   # returning False would abort training

    def _on_training_end(self) -> None:
        elapsed = time.time() - self._start_time
        print(f"\n  Training complete in {elapsed/60:.1f} min")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def make_env():
    """Factory that creates a monitored, time-limited SARExploreEnv."""
    env = SARExploreEnv()
    env = TimeLimit(env, max_episode_steps=MAX_STEPS)
    env = Monitor(env)
    return env


def train(total_steps: int, run_eval: bool = False):
    print(f"\n[Drishya PPO] Creating vectorised environment (4 parallel workers)...")
    vec_env = make_vec_env(make_env, n_envs=4)

    print("[Drishya PPO] Building PPO model...")
    model = PPO(
        policy             = "MlpPolicy",
        env                = vec_env,
        learning_rate      = 3e-4,
        n_steps            = 512,
        batch_size         = 64,
        n_epochs           = 10,
        gamma              = 0.99,
        gae_lambda         = 0.95,
        clip_range         = 0.2,
        ent_coef           = 0.01,    # encourage exploration
        vf_coef            = 0.5,
        max_grad_norm      = 0.5,
        tensorboard_log    = LOG_DIR,
        verbose            = 0,
    )

    callbacks = [TrainingProgressCallback(total_steps=total_steps)]

    if run_eval:
        eval_env = Monitor(SARExploreEnv())
        eval_cb  = EvalCallback(
            eval_env,
            best_model_save_path = MODEL_DIR,
            log_path             = LOG_DIR,
            eval_freq            = max(total_steps // 20, 5000),
            n_eval_episodes      = 5,
            verbose              = 0,
        )
        callbacks.append(eval_cb)

    print(f"[Drishya PPO] Starting training for {total_steps:,} steps...\n")
    model.learn(
        total_timesteps = total_steps,
        callback        = callbacks,
        progress_bar    = False,
    )

    model.save(MODEL_PATH)
    print(f"\n[Drishya PPO] ✓ Model saved → {MODEL_PATH}.zip")

    # Quick evaluation run
    print("\n[Drishya PPO] Running 5-episode evaluation...")
    eval_env = SARExploreEnv()
    ep_rewards, ep_explores = [], []

    for ep in range(5):
        obs, _ = eval_env.reset()
        ep_rew  = 0.0
        for _ in range(MAX_STEPS):
            action, _ = model.predict(obs, deterministic=True)
            obs, rew, term, trunc, info = eval_env.step(action)
            ep_rew += rew
            if term or trunc:
                break
        ep_rewards.append(ep_rew)
        ep_explores.append(info.get("explore_pct", 0.0))

    print(f"\n  Evaluation over 5 episodes:")
    print(f"  Mean reward      : {np.mean(ep_rewards):.1f}")
    print(f"  Mean exploration : {np.mean(ep_explores):.1f}%")
    print(f"  Best episode     : {max(ep_rewards):.1f}\n")

    return model


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Train PPO policy for Project Drishya SAR exploration"
    )
    parser.add_argument(
        "--steps", type=int, default=50_000,
        help="Total training timesteps (default: 50000 for quick demo)"
    )
    parser.add_argument(
        "--eval", action="store_true",
        help="Enable EvalCallback (saves best_model.zip separately)"
    )
    args = parser.parse_args()

    train(total_steps=args.steps, run_eval=args.eval)
