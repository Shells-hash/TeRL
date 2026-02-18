"""
Base task abstraction: reward, done, and info are defined by concrete tasks.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseTask(ABC):
    """
    Task controls reward, termination, and info.
    Environment remains generic; tasks define semantics.
    """

    @abstractmethod
    def compute_reward(
        self,
        prev_state: dict[str, Any],
        next_state: dict[str, Any],
        events: dict[str, Any],
    ) -> float:
        """Return step reward given state transition and optional events."""
        ...

    @abstractmethod
    def check_done(
        self,
        state: dict[str, Any],
        step_count: int,
        max_episode_steps: int,
    ) -> bool:
        """Return True if episode should end."""
        ...

    @abstractmethod
    def get_info(
        self,
        state: dict[str, Any],
        episode_reward: float,
        step_count: int,
    ) -> dict[str, Any]:
        """Return info dict for this step (episode_length, total_reward, etc.)."""
        ...
