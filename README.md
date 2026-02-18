# TeRL — Terraria RL TCP Bridge

Minimal TCP bridge for receiving JSON game state from a Terraria tModLoader mod. This is a foundation only: no RL or training logic.

## Setup

1. Create and activate a virtual environment (optional; the bridge uses only the standard library):

   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. No extra dependencies are required for the bridge. If you add them later:

   ```powershell
   pip install -r requirements.txt
   ```

## Running the bridge client

The bridge client connects to **localhost:8765** and continuously receives and prints JSON game state.

**Terminal 1 — start the server (mock or Terraria mod):**

```powershell
python mock_server.py
```

**Terminal 2 — run the bridge client:**

```powershell
python bridge_client.py
```

Options:

- `--host 127.0.0.1` — server host (default: 127.0.0.1)
- `--port 8765` — server port (default: 8765)
- `--no-request` — do not send a request line; only read (for push-based servers that send JSON without a request)
- `--debug` — log each request send and each chunk received (to diagnose "no data" from the Terraria server)

The client will reconnect automatically if the connection drops.

### Not receiving data from the Terraria server?

- **Push-based mod:** If the mod sends JSON on its own (no command from the client), run with `--no-request`:  
  `python bridge_client.py --no-request`
- **See where it stalls:** Run with `--debug`. You’ll see "Sent request: 'state'" then either "recv N bytes" (data arriving) or nothing (server not replying or not sending newline-terminated lines).
- The server must send **one JSON object per line**, with each line ending in `\n`.

## Testing the connection

To check that the server is reachable:

```powershell
python test_server_connection.py
```

To perform a request/response exchange (request state, send action 0, receive state again):

```powershell
python test_server_connection.py --exchange
```

## Expected JSON format

The server sends **newline-terminated** JSON lines. Each message is a single JSON object. The mock server uses a state object like:

```json
{
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
  "last_reward_events": {}
}
```

The Terraria mod can use the same shape or extend it; the bridge only parses JSON and prints the keys/values.

## Connecting to the Terraria mod

1. Run the Terraria tModLoader mod so it listens on **TCP port 8765** (e.g. on 127.0.0.1).
2. Run the bridge client on the same machine:

   ```powershell
   python bridge_client.py --host 127.0.0.1 --port 8765
   ```

3. If the mod **pushes** state (sends JSON lines without the client requesting them), use:

   ```powershell
   python bridge_client.py --no-request
   ```

4. If the mod is **request–response** (like the mock server), leave `--no-request` off so the client sends `state` (or the mod’s request command) before each read.

## Project layout

```
TeRL/
├── bridge_client.py      # Entry point: TCP client, receives JSON, prints state
├── mock_server.py        # Fake server for testing (localhost:8765)
├── test_server_connection.py  # Connection test script
├── requirements.txt
├── README.md
└── .gitignore
```

## Error handling

The bridge client:

- **Buffers partial TCP data** until a full newline-terminated line is received.
- **Catches JSON decode errors** and skips invalid lines with a message.
- **Handles disconnections** by closing the socket and optionally reconnecting after a short delay.

Next step: add RL logic on top of this bridge when ready.
