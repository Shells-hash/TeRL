"""
Gym-style environment wrapper for Terraria RL agent.
Wraps TerrariaClient; provides reset() and step(action) for training loops.
Uses only standard library. No training logic—networking and env interface only.
"""

from typing import Any

from src.client import TerrariaClient

# Server state schema (for reference and type hints):
# {
#   "player_x": float,
#   "player_y": float,
#   "velocity_x": float,
#   "velocity_y": float,
#   "health": int,
#   "max_health": int,
#   "mana": int,
#   "max_mana": int,
#   "on_ground": bool,
#   "time_of_day": float,
#   "nearby_npcs": list,
#   "reward": float,
#   "done": bool
# }


class TerrariaEnv:
    """
    Gym-style environment: reset() and step(action).
    Keeps a persistent connection to the Terraria mod server.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8765,
        timeout: float = 30.0,
    ):
        self._client = TerrariaClient(host=host, port=port, timeout=timeout)
        self._state: dict[str, Any] | None = None

    def reset(self) -> tuple[dict[str, Any], dict[str, Any]]:
        """
        Connect if needed and receive initial state from server.
        Returns (state, info).
        """
        self._client.connect()
        state = self._client.receive_state()
        self._state = state
        info = self._info_from_state(state, step_reward=0.0)
        print(f"[TerrariaEnv] reset() -> state keys: {list(state.keys())}")
        return state, info

    def step(self, action: int) -> tuple[dict[str, Any], float, bool, dict[str, Any]]:
        """
        Send action, receive next state, return (state, reward, done, info).
        """
        if self._state is None:
            raise RuntimeError("Call reset() before step()")
        action = int(action)
        self._client.send_action(action)
        next_state = self._client.receive_state()
        reward = next_state.get("reward", 0.0)
        done = next_state.get("done", False)
        self._state = next_state
        info = self._info_from_state(next_state, step_reward=reward)
        print(f"[TerrariaEnv] step(action={action}) -> reward={reward}, done={done}")
        return next_state, reward, done, info

    def _info_from_state(self, state: dict[str, Any], step_reward: float = 0.0) -> dict[str, Any]:
        """Build info dict for compatibility with training loops (e.g. SB3)."""
        return {
            "state": state,
            "reward": step_reward,
        }

    def close(self) -> None:
        """Close the client connection."""
        self._client.close()
        self._state = None
        print("[TerrariaEnv] closed")
