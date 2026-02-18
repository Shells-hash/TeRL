"""Task abstraction: reward, done, and info defined per task."""

from src.tasks.base_task import BaseTask
from src.tasks.locomotion import LocomotionTask
from src.tasks.survival import SurvivalTask
from src.tasks.task_factory import get_task
from src.tasks.wood_gather import WoodGatherTask

__all__ = [
    "BaseTask",
    "LocomotionTask",
    "WoodGatherTask",
    "SurvivalTask",
    "get_task",
]
