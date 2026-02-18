"""
Locomotion task: reward = delta player_x, done = max_steps only.
"""

from typing import Any

from src.tasks.base_task import BaseTask


class LocomotionTask(BaseTask):
    """
    Phase 1 task: learn to move right.
    Reward is delta player_x (optionally scaled); no early termination.
    """

    def __init__(self, max_episode_steps: int = 10_000, scale: float = 1.0):
        self.max_episode_steps = max_episode_steps
        self.scale = scale

    def compute_reward(
        self,
        prev_state: dict[str, Any],
        next_state: dict[str, Any],
        events: dict[str, Any],
    ) -> float:
        prev_x = prev_state.get("player_x", 0)
        next_x = next_state.get("player_x", 0)
        delta_x = next_x - prev_x
        return float(delta_x) * self.scale

    def check_done(
        self,
        state: dict[str, Any],
        step_count: int,
        max_episode_steps: int,
    ) -> bool:
        return step_count >= max_episode_steps

    def get_info(
        self,
        state: dict[str, Any],
        episode_reward: float,
        step_count: int,
    ) -> dict[str, Any]:
        return {
            "episode_length": step_count,
            "total_reward": episode_reward,
            "survival_time": step_count,
            "wood_collected": state.get("wood_count", 0),
        }
