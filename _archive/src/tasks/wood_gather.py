"""
Wood gather task (stub): reward = wood_count delta; done = max_steps or optional wood threshold.
"""

from typing import Any

from src.tasks.base_task import BaseTask


class WoodGatherTask(BaseTask):
    """
    Reward for collecting wood; done at max_steps or when wood_threshold reached (if set).
    """

    def __init__(
        self,
        max_episode_steps: int = 10_000,
        wood_threshold: int | None = None,
        reward_per_wood: float = 1.0,
    ):
        self.max_episode_steps = max_episode_steps
        self.wood_threshold = wood_threshold
        self.reward_per_wood = reward_per_wood

    def compute_reward(
        self,
        prev_state: dict[str, Any],
        next_state: dict[str, Any],
        events: dict[str, Any],
    ) -> float:
        prev_wood = prev_state.get("wood_count", 0)
        next_wood = next_state.get("wood_count", 0)
        return (next_wood - prev_wood) * self.reward_per_wood

    def check_done(
        self,
        state: dict[str, Any],
        step_count: int,
        max_episode_steps: int,
    ) -> bool:
        if step_count >= max_episode_steps:
            return True
        if self.wood_threshold is not None and state.get("wood_count", 0) >= self.wood_threshold:
            return True
        return False

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
