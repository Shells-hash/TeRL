"""
Minimal TCP bridge client for Terraria RL.
Connects to localhost:8765, receives newline-terminated JSON game state,
and prints parsed state. Handles partial packets, JSON errors, and disconnections.
"""

import json
import socket
import sys
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
RECV_SIZE = 4096


def _format_state(state: dict) -> str:
    """Format a state dict for readable console output."""
    lines = ["--- Game state ---"]
    for key, value in sorted(state.items()):
        if key == "last_reward_events" and isinstance(value, dict):
            if value:
                lines.append(f"  {key}: {value}")
            continue
        lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def _recv_until_newline(
    sock: socket.socket, buf: bytearray, debug: bool = False
) -> tuple[str | None, bytearray]:
    """
    Read from socket until a newline; buffer partial data in buf.
    Returns (decoded line or None if connection closed, updated buffer).
    """
    while True:
        idx = buf.find(b"\n")
        if idx != -1:
            line_b = bytes(buf[:idx])
            del buf[: idx + 1]
            if debug:
                print(f"[Bridge] Received line ({len(line_b)} bytes)", flush=True)
            return line_b.decode("utf-8").strip(), buf
        try:
            data = sock.recv(RECV_SIZE)
        except (ConnectionResetError, BrokenPipeError, OSError, socket.timeout) as e:
            if debug:
                print(f"[Bridge] recv error: {e}", flush=True)
            return None, buf
        if not data:
            if debug:
                print("[Bridge] recv returned 0 (connection closed)", flush=True)
            return None, buf
        if debug:
            print(f"[Bridge] recv {len(data)} bytes (buffer now {len(buf) + len(data)} bytes, no newline yet)", flush=True)
        buf.extend(data)


def run_bridge(
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    request_state_line: str | None = None,
    debug: bool = False,
) -> None:
    """
    Connect to the game server and continuously receive and print JSON state.
    - request_state_line: if set (e.g. "state"), send this line before each read
      so the server sends a state (mock server / request-response protocol).
      If None, only read (for push-based servers that send JSON lines without request).
    - debug: print when sending requests and when receiving raw bytes (for diagnosing no data).
    """
    buf = bytearray()
    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30.0)
            sock.connect((host, port))
            print(f"[Bridge] Connected to {host}:{port}", flush=True)
        except (ConnectionRefusedError, OSError) as e:
            print(f"[Bridge] Connection failed: {e}. Retrying in 5s...", flush=True)
            try:
                time.sleep(5)
            except KeyboardInterrupt:
                sys.exit(0)
            continue

        buf.clear()
        try:
            while True:
                line, buf = _recv_until_newline(sock, buf, debug=debug)
                if line is None:
                    print("[Bridge] Connection closed by server.", flush=True)
                    break
                if not line:
                    continue
                try:
                    state = json.loads(line)
                except json.JSONDecodeError as e:
                    print(f"[Bridge] JSON decode error: {e} (skipping line)", flush=True)
                    continue
                print(_format_state(state), flush=True)
        except KeyboardInterrupt:
            print("\n[Bridge] Stopped by user.", flush=True)
            break
        finally:
            try:
                sock.close()
            except OSError:
                pass
        # Reconnect after disconnect
        print("[Bridge] Reconnecting in 2s...", flush=True)
        try:
            time.sleep(2)
        except KeyboardInterrupt:
            sys.exit(0)


class BridgeClient:
    """
    Minimal TCP client: connect, request state (send 'state'), optionally send action, receive JSON.
    Used by test_server_connection and for one-off requests.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = 5.0,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        if self._sock is not None:
            try:
                self._sock.getpeername()
                return
            except OSError:
                self._sock = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.host, self.port))

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def request_state(self) -> dict:
        """Send 'state', receive one newline-terminated JSON line, return parsed dict."""
        if self._sock is None:
            raise ConnectionError("Not connected")
        buf = bytearray()
        line, _ = _recv_until_newline(self._sock, buf)
        if line is None:
            raise ConnectionError("Connection closed")
        return json.loads(line)

    def send_action(self, action: int) -> dict:
        """Send newline-terminated JSON {\"action_id\": N}, receive one JSON line (state), return parsed dict. Only action_id is sent; no state sent to the mod."""
        if self._sock is None:
            raise ConnectionError("Not connected")
        action_obj = {"action_id": int(action)}
        message = json.dumps(action_obj) + "\n"
        print("SENDING TO MOD:", message)
        self._sock.sendall(message.encode("utf-8"))
        buf = bytearray()
        line, _ = _recv_until_newline(self._sock, buf)
        if line is None:
            raise ConnectionError("Connection closed")
        return json.loads(line)


def connect_and_receive_one(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> dict | None:
    """
    Connect, request one state (send "state"), receive one JSON line, close.
    Returns parsed state dict or None on failure. Used by test_server_connection.
    """
    client = BridgeClient(host=host, port=port)
    try:
        client.connect()
        return client.request_state()
    except (ConnectionRefusedError, OSError, json.JSONDecodeError, ConnectionError):
        return None
    finally:
        client.close()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Terraria TCP bridge client: receive JSON game state.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Server host")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Server port")
    parser.add_argument(
        "--no-request",
        action="store_true",
        help="Do not send a request line; only read (push-based server).",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print when sending requests and receiving bytes (diagnose no data).",
    )
    args = parser.parse_args()
    request_line = None if args.no_request else "state"
    run_bridge(host=args.host, port=args.port, request_state_line=request_line, debug=args.debug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
