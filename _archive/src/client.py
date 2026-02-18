"""
Persistent TCP socket client for Terraria tModLoader RL mod.
Connects to localhost:8765, receives JSON state messages, sends JSON action messages.
Uses only standard library: socket, json, time.
"""

import json
import socket
import time
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_TIMEOUT = 30.0
RECONNECT_ATTEMPTS = 5
RECONNECT_DELAY_SEC = 1.0


class TerrariaClient:
    """
    Persistent TCP client for Terraria RL environment.
    - connect(): establish connection (idempotent if already connected).
    - receive_state(): read one newline-terminated JSON state from server.
    - send_action(action: int): send {"action": action} as JSON line.
    - close(): close the connection.
    Reconnects automatically on connection loss when receive_state/send_action are used.
    """

    def __init__(
        self,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
        reconnect_attempts: int = RECONNECT_ATTEMPTS,
        reconnect_delay: float = RECONNECT_DELAY_SEC,
    ):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.reconnect_attempts = reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self._sock: socket.socket | None = None

    def connect(self) -> None:
        """Open a persistent TCP connection to the server. Idempotent if already connected."""
        if self._sock is not None:
            try:
                self._sock.getpeername()
                return
            except OSError:
                self._sock = None
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(self.timeout)
        self._sock.connect((self.host, self.port))
        print(f"[TerrariaClient] Connected to {self.host}:{self.port}")

    def close(self) -> None:
        """Close the connection."""
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
            print("[TerrariaClient] Connection closed")

    def _is_connected(self) -> bool:
        if self._sock is None:
            return False
        try:
            self._sock.getpeername()
            return True
        except OSError:
            return False

    def _recv_line(self) -> str:
        """Receive a newline-terminated line. Raises ConnectionError if not connected or connection closed."""
        if self._sock is None:
            raise ConnectionError("Not connected")
        buf = []
        while True:
            b = self._sock.recv(1)
            if not b:
                raise ConnectionError("Connection closed by server")
            if b == b"\n":
                break
            buf.append(b)
        return b"".join(buf).decode("utf-8")

    def _send_line(self, line: str) -> None:
        """Send a newline-terminated line. Raises ConnectionError if not connected."""
        if self._sock is None:
            raise ConnectionError("Not connected")
        self._sock.sendall((line + "\n").encode("utf-8"))

    def receive_state(self) -> dict[str, Any]:
        """
        Receive one JSON state message from the server.
        On connection failure, attempts reconnect up to reconnect_attempts times.
        """
        last_err: Exception | None = None
        for attempt in range(self.reconnect_attempts):
            try:
                if not self._is_connected():
                    self.connect()
                raw = self._recv_line()
                state = json.loads(raw)
                return state
            except (ConnectionError, json.JSONDecodeError, OSError, socket.timeout) as e:
                last_err = e
                self._sock = None
                if attempt < self.reconnect_attempts - 1:
                    print(f"[TerrariaClient] receive_state failed (attempt {attempt + 1}): {e}; reconnecting in {self.reconnect_delay}s")
                    time.sleep(self.reconnect_delay)
        raise ConnectionError(f"receive_state failed after {self.reconnect_attempts} attempts") from last_err

    def send_action(self, action: int) -> None:
        """
        Send a JSON action message: {"action": action}.
        On connection failure, attempts reconnect up to reconnect_attempts times.
        """
        action = int(action)
        payload = json.dumps({"action": action})
        last_err: Exception | None = None
        for attempt in range(self.reconnect_attempts):
            try:
                if not self._is_connected():
                    self.connect()
                self._send_line(payload)
                return
            except (ConnectionError, OSError, socket.timeout) as e:
                last_err = e
                self._sock = None
                if attempt < self.reconnect_attempts - 1:
                    print(f"[TerrariaClient] send_action failed (attempt {attempt + 1}): {e}; reconnecting in {self.reconnect_delay}s")
                    time.sleep(self.reconnect_delay)
        raise ConnectionError(f"send_action failed after {self.reconnect_attempts} attempts") from last_err

    def get_state(self) -> dict[str, Any]:
        """Alias for receive_state to match environment interface."""
        return self.receive_state()
