# Terraria RL Environment (Milestone 1)

Gym-style environment for an AI agent that learns to survive the first night in Terraria. This milestone provides a clean, modular environment interface with a mock Terraria backend (no deep learning yet).

## Setup

1. Create and activate a virtual environment (if not already done):

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

## Running

**Option A — Two terminals**

- Terminal 1: start the mock server  
  `python mock_server.py`
- Terminal 2: run the random agent test (10 episodes)  
  `python test_random_agent.py`

**Option B — Single run**

- `python test_random_agent.py` starts the mock server in a subprocess and then runs 10 episodes.

From the project root, either:

```powershell
python mock_server.py
```

then in another terminal:

```powershell
python test_random_agent.py
```

or just:

```powershell
python test_random_agent.py
```

## Project layout

- `src/environment.py` — `TerrariaEnv`: `reset()`, `step(action)`, observation space, termination.
- `src/reward.py` — Shaped reward calculation (wood, tree, shelter, damage, death, survived night).
- `src/client.py` — Socket I/O: connect, get state, send action (0–6).
- `mock_server.py` — Fake Terraria server on localhost:8765; serves JSON state and applies actions.
- `test_random_agent.py` — Runs random actions for 10 episodes and prints per-episode stats.

## Observation and actions

- **Observation vector**: `[player_x, player_y, health, wood_count, is_night, enemy_distance, enemy_count]`
- **Actions**: 0=left, 1=right, 2=jump, 3=mine, 4=place_block, 5=attack, 6=do_nothing

## Rewards (shaped)

- +2 wood collected, +5 tree chopped, +50 shelter built  
- -10 damage taken, -100 death, +200 survived night

## Curriculum: learn to move first

Before training "survive the night", you can train on a simpler task: **move right**. The agent gets reward for moving right and a bonus for reaching a target x; episodes end when `player_x >= target` or at max steps.

- **Task** `"move_right"`: reward +1 per step moving right, +10 for reaching target x; done when `player_x >= move_right_target_x` (default 10).
- **Task** `"survive_night"` (default): full shaped rewards and termination (death, survived night, max steps).

Example:

```python
from src.environment import TerrariaEnv, TASK_MOVE_RIGHT

env = TerrariaEnv(port=8765, task=TASK_MOVE_RIGHT, move_right_target_x=10.0)
obs, info = env.reset()
# ... step with action 1 (move_right) to get reward
```

Or run the random agent with the move-right task (episodes will often end sooner when the agent drifts right):

```powershell
python test_random_agent.py --move-right
```

## Next steps (out of scope for M1)

Imitation learning, PPO fine-tuning, curriculum learning, and hierarchical planning will build on this environment.
