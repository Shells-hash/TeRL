"""
Test that the Terraria / mock server is reachable on localhost:8765.
Uses the bridge client; exits 0 on success, 1 on failure.

Usage:
  python test_server_connection.py
  python test_server_connection.py --host 127.0.0.1 --port 8765
  python test_server_connection.py --exchange   # connect, receive one state, send one action, receive again
"""

import argparse
import sys

from bridge_client import BridgeClient

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def main() -> int:
    parser = argparse.ArgumentParser(description="Test server connection for Terraria RL.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument(
        "--exchange",
        action="store_true",
        help="After connect: request_state(), send_action(0), request_state(); requires server to accept 'state' and '0'-'6'.",
    )
    args = parser.parse_args()

    client = BridgeClient(host=args.host, port=args.port, timeout=5.0)
    try:
        client.connect()
        print(f"OK Connected to {args.host}:{args.port}")
    except (ConnectionRefusedError, OSError) as e:
        print(f"FAIL Could not connect to {args.host}:{args.port}: {e}", file=sys.stderr)
        return 1

    if args.exchange:
        try:
            state = client.request_state()
            print(f"  request_state() -> keys: {list(state.keys())}")
            next_state = client.send_action(0)
            print(f"  send_action(0) -> keys: {list(next_state.keys())}")
        except Exception as e:
            print(f"FAIL Exchange failed: {e}", file=sys.stderr)
            client.close()
            return 1

    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
