"""
Evaluate a saved PPO model: run deterministic policy, print episode reward, survival time, wood collected.
Starts mock_server in a subprocess.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

from stable_baselines3 import PPO

from src.environment import TerrariaEnv
from src.tasks import get_task

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8765
MAX_EPISODE_STEPS = 10_000


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate saved PPO model.")
    parser.add_argument("--model-path", type=str, required=True, help="Path to model .zip")
    parser.add_argument("--task", type=str, default="locomotion", help="Task (must match training)")
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    proc = subprocess.Popen(
        [sys.executable, "mock_server.py", str(args.port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.5)
        model = PPO.load(args.model_path)
        task = get_task(args.task, max_episode_steps=MAX_EPISODE_STEPS)
        env = TerrariaEnv(port=args.port, max_episode_steps=MAX_EPISODE_STEPS, task=task)

        for ep in range(1, args.episodes + 1):
            obs, info = env.reset()
            total_reward = 0.0
            done = False
            while not done:
                action, _ = model.predict(obs, deterministic=True)
                obs, reward, terminated, truncated, info = env.step(int(action))
                total_reward += reward
                done = terminated or truncated

            print(
                f"Episode {ep}: reward={total_reward:.1f} "
                f"survival_time={info.get('survival_time', 0)} "
                f"wood_collected={info.get('wood_collected', 0)}"
            )
        env.close()
    finally:
        proc.terminate()
        proc.wait(timeout=2)


if __name__ == "__main__":
    main()
