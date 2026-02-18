"""
Gym-style Terraria environment: reset(), step(action), structured observation.
Reward, done, and info are delegated to the task object.
"""

import numpy as np
from typing import Any

import gymnasium as gym

from src.client import TerrariaClient
from src.tasks.base_task import BaseTask


# Observation vector order (fixed for indexing)
OBS_KEYS = [
    "player_x",
    "player_y",
    "health",
    "wood_count",
    "is_night",
    "enemy_distance",
    "enemy_count",
]

NUM_ACTIONS = 7
MAX_EPISODE_STEPS = 10_000

# Bounds for Box space (finite for SB3)
OBS_LOW = np.array([-1e4] * len(OBS_KEYS), dtype=np.float32)
OBS_HIGH = np.array([1e4] * len(OBS_KEYS), dtype=np.float32)


def _state_to_obs(state: dict[str, Any]) -> np.ndarray:
    """Build observation vector from state dict."""
    vals = []
    for k in OBS_KEYS:
        v = state.get(k, 0)
        if isinstance(v, bool):
            v = 1 if v else 0
        vals.append(float(v))
    return np.array(vals, dtype=np.float32)


class TerrariaEnv(gym.Env):
    """
    Generic Terraria env: task controls reward, termination, and info.
    reset() -> (obs, info); step(action) -> (obs, reward, terminated, truncated, info).
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8765,
        max_episode_steps: int = MAX_EPISODE_STEPS,
        task: BaseTask | None = None,
    ):
        if task is None:
            raise ValueError("task must be a BaseTask instance (e.g. get_task('locomotion')).")
        super().__init__()
        self.client = TerrariaClient(host=host, port=port)
        self.max_episode_steps = max_episode_steps
        self.task = task
        self._state: dict[str, Any] | None = None
        self._step_count = 0
        self._episode_reward = 0.0

        self.observation_space = gym.spaces.Box(
            low=OBS_LOW,
            high=OBS_HIGH,
            shape=(len(OBS_KEYS),),
            dtype=np.float32,
        )
        self.action_space = gym.spaces.Discrete(NUM_ACTIONS)

    def reset(
        self,
        seed: int | None = None,
        options: dict | None = None,
    ) -> tuple[np.ndarray, dict]:
        self._step_count = 0
        self._episode_reward = 0.0
        state = self.client.get_state()
        if state is None:
            raise RuntimeError("Failed to get initial state from server (is mock_server running?)")
        self._state = state
        obs = _state_to_obs(state)
        info = self.task.get_info(state, 0.0, 0)
        return obs, info

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        if self._state is None:
            raise RuntimeError("Call reset() before step()")
        action = int(action)
        if not 0 <= action < NUM_ACTIONS:
            action = 6

        prev_state = dict(self._state)
        next_state = self.client.send_action(action)
        if next_state is None:
            raise RuntimeError("Failed to get state after action (connection lost?)")

        self._state = next_state
        self._step_count += 1

        events = next_state.get("last_reward_events", {})
        reward = self.task.compute_reward(prev_state, next_state, events)
        self._episode_reward += reward

        done = self.task.check_done(next_state, self._step_count, self.max_episode_steps)
        # Gymnasium: terminated = game over, truncated = time limit (we don't separate yet)
        terminated = done
        truncated = False

        info = self.task.get_info(next_state, self._episode_reward, self._step_count)
        obs = _state_to_obs(next_state)
        return obs, reward, terminated, truncated, info

    def close(self) -> None:
        self.client.close()
