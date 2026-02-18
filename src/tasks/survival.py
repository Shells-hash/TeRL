"""
Survival task: shaped rewards (wood, damage, death, survived_night); done on death, survived_night, or max_steps.
"""

from typing import Any

from src.reward import compute_reward
from src.tasks.base_task import BaseTask


class SurvivalTask(BaseTask):
    """
    Full survive-first-night task: shaped rewards, termination on death or survived night.
    """

    def __init__(self, max_episode_steps: int = 10_000):
        self.max_episode_steps = max_episode_steps

    def compute_reward(
        self,
        prev_state: dict[str, Any],
        next_state: dict[str, Any],
        events: dict[str, Any],
    ) -> float:
        return compute_reward(prev_state, next_state, events)

    def check_done(
        self,
        state: dict[str, Any],
        step_count: int,
        max_episode_steps: int,
    ) -> bool:
        if step_count >= max_episode_steps:
            return True
        if state.get("health", 0) <= 0:
            return True
        if state.get("last_reward_events", {}).get("survived_night"):
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
