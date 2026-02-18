"""
Factory to get task by name. Single place to add new tasks.
"""

from src.tasks.base_task import BaseTask
from src.tasks.locomotion import LocomotionTask
from src.tasks.survival import SurvivalTask
from src.tasks.wood_gather import WoodGatherTask


def get_task(
    name: str,
    max_episode_steps: int = 10_000,
    **kwargs: object,
) -> BaseTask:
    """
    Return a task instance by name.
    name: "locomotion" | "wood" | "survival"
    """
    name = name.lower().strip()
    if name == "locomotion":
        return LocomotionTask(max_episode_steps=max_episode_steps, **kwargs)
    if name == "wood":
        return WoodGatherTask(max_episode_steps=max_episode_steps, **kwargs)
    if name == "survival":
        return SurvivalTask(max_episode_steps=max_episode_steps, **kwargs)
    raise ValueError(f"Unknown task: {name!r}. Use locomotion, wood, or survival.")
