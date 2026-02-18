"""
Reward calculation for Terraria survive-first-night environment.
All magic numbers in one place; stateless.
"""

# Shaped reward constants (from spec)
REWARD_WOOD_COLLECTED = 2
REWARD_TREE_CHOPPED = 5
REWARD_SHELTER_BUILT = 50
REWARD_DAMAGE_TAKEN = -10
REWARD_DEATH = -100
REWARD_SURVIVED_NIGHT = 200

# Curriculum: movement-only task (learn to move before surviving night)
REWARD_MOVE_RIGHT = 1.0
REWARD_REACH_TARGET_X = 10.0


def compute_reward(
    prev_state: dict,
    next_state: dict,
    events: dict | None = None,
) -> float:
    """
    Compute step reward from state transition and optional events.

    Args:
        prev_state: State dict before the step (e.g. player_x, health, wood_count, etc.).
        next_state: State dict after the step.
        events: Optional dict of event flags from server, e.g.:
            wood_collected, tree_chopped, shelter_built, damage_taken, died, survived_night.

    Returns:
        Scalar reward for this step.
    """
    events = events or {}
    reward = 0.0

    if events.get("wood_collected"):
        reward += REWARD_WOOD_COLLECTED
    if events.get("tree_chopped"):
        reward += REWARD_TREE_CHOPPED
    if events.get("shelter_built"):
        reward += REWARD_SHELTER_BUILT
    if events.get("damage_taken"):
        reward += REWARD_DAMAGE_TAKEN
    if events.get("died"):
        reward += REWARD_DEATH
    if events.get("survived_night"):
        reward += REWARD_SURVIVED_NIGHT

    # Fallback: infer from state deltas if events not provided
    if not events:
        prev_health = prev_state.get("health", 0)
        next_health = next_state.get("health", 0)
        if next_health < prev_health:
            reward += REWARD_DAMAGE_TAKEN
        if next_health <= 0 and prev_health > 0:
            reward += REWARD_DEATH

        prev_wood = prev_state.get("wood_count", 0)
        next_wood = next_state.get("wood_count", 0)
        if next_wood > prev_wood:
            reward += REWARD_WOOD_COLLECTED

        prev_night = prev_state.get("is_night", False)
        next_night = next_state.get("is_night", False)
        if prev_night and not next_night and next_health > 0:
            reward += REWARD_SURVIVED_NIGHT

    return reward


def compute_reward_move_right(
    prev_state: dict,
    next_state: dict,
    target_x: float,
) -> float:
    """
    Reward for curriculum task "move right": reward for increasing player_x,
    plus bonus when reaching target_x. Use this before training survive_night.
    """
    reward = 0.0
    prev_x = prev_state.get("player_x", 0)
    next_x = next_state.get("player_x", 0)
    delta_x = next_x - prev_x
    if delta_x > 0:
        reward += REWARD_MOVE_RIGHT
    if prev_x < target_x <= next_x:
        reward += REWARD_REACH_TARGET_X
    return reward
