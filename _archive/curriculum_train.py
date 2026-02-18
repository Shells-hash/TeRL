"""
Curriculum training: locomotion -> wood -> survival.
Weights carry forward between stages. Phase 1: structure only; run locomotion stage only.

Planned flow:
  1. Train locomotion -> save
  2. Load model -> switch to wood task -> continue training -> save
  3. Load model -> switch to survival task -> continue training -> save
"""

import argparse
import sys
import time
from pathlib import Path

# When implementing full curriculum:
# from stable_baselines3 import PPO
# from src.environment import TerrariaEnv
# from src.tasks import get_task

PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_PORT = 8765
MAX_EPISODE_STEPS = 10_000
STAGE_TIMESTEPS = 50_000


def main() -> None:
    parser = argparse.ArgumentParser(description="Curriculum train (structure: locomotion -> wood -> survival).")
    parser.add_argument("--stage", type=str, default="locomotion", choices=["locomotion", "wood", "survival"],
                        help="Which stage to run (Phase 1: only locomotion is runnable)")
    parser.add_argument("--timesteps", type=int, default=STAGE_TIMESTEPS)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--load-path", type=str, default=None, help="Load previous stage model (for future use)")
    parser.add_argument("--save-path", type=str, default=None)
    args = parser.parse_args()

    # Phase 1: run locomotion stage only (same as train.py --task locomotion)
    if args.stage == "locomotion":
        from train import main as train_main
        sys.argv = [
            "train.py",
            "--task", "locomotion",
            "--timesteps", str(args.timesteps),
            "--port", str(args.port),
        ]
        if args.save_path:
            sys.argv.extend(["--save-path", args.save_path])
        train_main()
        return

    # Future: load model, set env to next task, learn, save
    # model = PPO.load(args.load_path)
    # task = get_task(args.stage, max_episode_steps=MAX_EPISODE_STEPS)
    # env = TerrariaEnv(port=args.port, task=task)
    # model.set_env(env)
    # model.learn(total_timesteps=args.timesteps)
    # model.save(args.save_path or f"models/{args.stage}")
    print("Only --stage locomotion is implemented in Phase 1. Use train.py for locomotion.")


if __name__ == "__main__":
    main()
