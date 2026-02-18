"""
Train PPO on Terraria env. Task controls reward and termination.
Starts mock_server in a subprocess if not already running.

Usage:
  python train.py --task locomotion --timesteps 50000
  python train.py --task wood --timesteps 30000 --save-path models/wood
"""

import argparse
import sys
import time
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

from src.environment import TerrariaEnv
from src.tasks import get_task

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8765
MAX_EPISODE_STEPS = 10_000
DEFAULT_TIMESTEPS = 50_000


def make_env(port: int, task_name: str):
    """Factory for TerrariaEnv with given task."""
    task = get_task(task_name, max_episode_steps=MAX_EPISODE_STEPS)
    def _init():
        return TerrariaEnv(port=port, max_episode_steps=MAX_EPISODE_STEPS, task=task)
    return _init


def main() -> None:
    parser = argparse.ArgumentParser(description="Train PPO on Terraria task.")
    parser.add_argument("--task", type=str, default="locomotion", help="Task: locomotion, wood, survival")
    parser.add_argument("--timesteps", type=int, default=DEFAULT_TIMESTEPS, help="Total training timesteps")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Mock server port")
    parser.add_argument("--save-path", type=str, default=None, help="Model save path (default: models/<task>)")
    parser.add_argument("--n-envs", type=int, default=1, help="Number of parallel envs (default 1)")
    args = parser.parse_args()

    save_path = args.save_path or f"models/{args.task}"
    if not save_path.endswith(".zip"):
        save_path = save_path.rstrip("/")

    # Start mock server in subprocess
    import subprocess
    proc = subprocess.Popen(
        [sys.executable, "mock_server.py", str(args.port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.5)
        if args.n_envs == 1:
            task = get_task(args.task, max_episode_steps=MAX_EPISODE_STEPS)
            env = TerrariaEnv(port=args.port, max_episode_steps=MAX_EPISODE_STEPS, task=task)
        else:
            env = make_vec_env(
                make_env(args.port, args.task),
                n_envs=args.n_envs,
            )

        model = PPO(
            "MlpPolicy",
            env,
            verbose=1,
            policy_kwargs=dict(net_arch=[64, 64]),
        )
        model.learn(total_timesteps=args.timesteps)
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        model.save(save_path)
        print(f"Saved model to {save_path}")
        env.close()
    finally:
        proc.terminate()
        proc.wait(timeout=2)


if __name__ == "__main__":
    main()
