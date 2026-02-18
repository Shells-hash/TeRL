"""
Run random actions for 10 episodes to verify env + mock + task pipeline.
Starts mock server in a subprocess, then runs TerrariaEnv with random agent.

Usage:
  python test_random_agent.py              # survival task
  python test_random_agent.py --move-right # locomotion task
"""

import argparse
import random
import subprocess
import sys
import time
from pathlib import Path

from src.environment import TerrariaEnv
from src.tasks import get_task

MOCK_PORT = 8765
NUM_EPISODES = 10
MAX_EPISODE_STEPS = 200  # short episodes for quick smoke test
PROJECT_ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run random agent for N episodes.")
    parser.add_argument(
        "--move-right",
        action="store_true",
        help="Use locomotion task (reward = delta player_x)",
    )
    args = parser.parse_args()

    task_name = "locomotion" if args.move_right else "survival"
    task = get_task(task_name, max_episode_steps=MAX_EPISODE_STEPS)

    proc = subprocess.Popen(
        [sys.executable, "mock_server.py", str(MOCK_PORT)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        time.sleep(0.5)
        env = TerrariaEnv(port=MOCK_PORT, max_episode_steps=MAX_EPISODE_STEPS, task=task)
        random.seed(42)

        for ep in range(1, NUM_EPISODES + 1):
            obs, info = env.reset()
            done = False
            while not done:
                action = random.randint(0, 6)
                obs, reward, terminated, truncated, info = env.step(action)
                done = terminated or truncated

            extra = f" wood_collected={info['wood_collected']}" if task_name == "survival" else ""
            print(
                f"Episode {ep}: length={info['episode_length']} "
                f"total_reward={info['total_reward']:.1f} "
                f"survival_time={info['survival_time']}{extra}"
            )
        env.close()
    finally:
        proc.terminate()
        proc.wait(timeout=2)


if __name__ == "__main__":
    main()
