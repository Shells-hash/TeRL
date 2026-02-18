"""
Mock Terraria server: serves JSON state over TCP (localhost:8765).
Simulates state updates from actions; deterministic when seeded.
"""

import json
import random
import socket
import threading

DEFAULT_PORT = 8765
STEP_PER_DAY_NIGHT = 50  # steps before flipping is_night (simple cycle)


def _default_state(seed: int | None = None) -> dict:
    rng = random.Random(seed)
    return {
        "player_x": 0.0,
        "player_y": 0.0,
        "health": 100,
        "wood_count": 0,
        "is_night": 0,
        "enemy_distance": 100.0,
        "enemy_count": 0,
        "time_of_day": 0,
        "has_shelter": 0,
        "step_count": 0,
        "last_reward_events": {},
    }


def _apply_action(state: dict, action: int, rng: random.Random) -> dict:
    """Apply action to state; return new state and set last_reward_events."""
    state = dict(state)
    events = {}

    # Movement
    if action == 0:
        state["player_x"] = state["player_x"] - 1.0
    elif action == 1:
        state["player_x"] = state["player_x"] + 1.0
    elif action == 2:
        state["player_y"] = min(state["player_y"] + 2.0, 10.0)

    # Mine (action 3): gain wood, sometimes "tree chopped"
    elif action == 3:
        state["wood_count"] = state["wood_count"] + 1
        events["wood_collected"] = True
        if rng.random() < 0.2:
            state["wood_count"] = state["wood_count"] + 2
            events["tree_chopped"] = True

    # Place block (action 4): with enough wood, can build shelter
    elif action == 4:
        if state["wood_count"] >= 10 and not state.get("has_shelter"):
            state["wood_count"] = state["wood_count"] - 10
            state["has_shelter"] = 1
            events["shelter_built"] = True

    # Attack (action 5): reduce enemy count / distance (simplified)
    elif action == 5:
        if state["enemy_count"] > 0:
            state["enemy_count"] = max(0, state["enemy_count"] - 1)
            state["enemy_distance"] = min(100.0, state["enemy_distance"] + 10.0)

    # action 6: do_nothing

    # Day/night cycle
    state["step_count"] = state["step_count"] + 1
    old_night = state["is_night"]
    if state["step_count"] % STEP_PER_DAY_NIGHT == 0:
        state["is_night"] = 1 if state["is_night"] == 0 else 0
        state["time_of_day"] = state["step_count"] % (2 * STEP_PER_DAY_NIGHT)
        if old_night == 1 and state["is_night"] == 0:
            events["survived_night"] = True

    # At night: spawn enemies, possible damage
    if state["is_night"]:
        if rng.random() < 0.15:
            state["enemy_count"] = min(5, state["enemy_count"] + 1)
            state["enemy_distance"] = max(0.0, state["enemy_distance"] - 5.0)
        if state["enemy_count"] > 0 and state["enemy_distance"] < 20 and rng.random() < 0.2:
            state["health"] = max(0, state["health"] - 10)
            events["damage_taken"] = True
    else:
        state["enemy_count"] = 0
        state["enemy_distance"] = 100.0

    if state["health"] <= 0:
        events["died"] = True

    state["last_reward_events"] = events
    return state


def _handle_client(conn: socket.socket, addr: tuple, seed: int | None) -> None:
    rng = random.Random(seed)
    state = _default_state(seed)
    buf = b""
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode("utf-8").strip()
                if cmd == "state":
                    conn.sendall((json.dumps(state) + "\n").encode("utf-8"))
                elif cmd.isdigit() and 0 <= int(cmd) <= 6:
                    action = int(cmd)
                    state = _apply_action(state, action, rng)
                    conn.sendall((json.dumps(state) + "\n").encode("utf-8"))
                else:
                    conn.sendall((json.dumps(state) + "\n").encode("utf-8"))
    except (ConnectionResetError, BrokenPipeError, OSError):
        pass
    finally:
        conn.close()


def run_server(port: int = DEFAULT_PORT, seed: int | None = 42) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", port))
    server.listen(1)
    print(f"Mock Terraria server listening on 127.0.0.1:{port} (seed={seed})")

    while True:
        conn, addr = server.accept()
        # Each client gets a deterministic but distinct stream (seed + client port)
        client_seed = (seed or 0) + (addr[1] % 10000)
        t = threading.Thread(target=_handle_client, args=(conn, addr, client_seed))
        t.daemon = True
        t.start()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PORT
    run_server(port=port)
