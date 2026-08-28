from __future__ import annotations

import json
import socket
import time
from abc import ABC, abstractmethod
from typing import Any

from pocket_adsb.models.position import Position


class PositionSource(ABC):
    @abstractmethod
    def get_position(self) -> Position | None:
        """Return our current position, or None if unavailable."""
        pass

    @abstractmethod
    def status_text(self) -> str:
        """Return a short description of the position source state."""
        pass


class FixedPositionSource(PositionSource):
    def __init__(
        self,
        latitude: float,
        longitude: float,
    ) -> None:
        self.position = Position(
            latitude=latitude,
            longitude=longitude,
        )

    def get_position(self) -> Position:
        return self.position

    def status_text(self) -> str:
        return "FIXED"


class GpsdPositionSource(PositionSource):
    """Position source backed by a local gpsd instance.

    A valid live GPS fix is preferred. If the fix is lost after one has been
    acquired, the last good GPS position is retained. Until the first GPS fix,
    an optional fallback position can be used for range/bearing calculations.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 2947,
        fallback_position: Position | None = None,
        reconnect_seconds: float = 5.0,
        stale_seconds: float = 5.0,
    ) -> None:
        self.host = host
        self.port = port
        self.fallback_position = fallback_position
        self.reconnect_seconds = reconnect_seconds
        self.stale_seconds = stale_seconds

        self._socket: socket.socket | None = None
        self._buffer = ""
        self._last_connect_attempt = 0.0

        self._last_good_position: Position | None = None
        self._last_fix_monotonic: float | None = None
        self._last_mode = 1
        self._connected = False

    def get_position(self) -> Position | None:
        self._poll()

        if self._last_good_position is not None:
            return self._last_good_position

        return self.fallback_position

    def status_text(self) -> str:
        self._poll()

        if not self._connected:
            return "OFF"

        if self._last_fix_monotonic is not None:
            age = time.monotonic() - self._last_fix_monotonic

            if age <= self.stale_seconds:
                if self._last_mode >= 3:
                    return "3D"

                if self._last_mode == 2:
                    return "2D"

            return "LAST"

        return "NO FIX"

    def close(self) -> None:
        self._disconnect()

    def _poll(self) -> None:
        if self._socket is None:
            self._connect_if_due()

        if self._socket is None:
            return

        while True:
            try:
                chunk = self._socket.recv(4096)
            except BlockingIOError:
                break
            except (ConnectionError, OSError):
                self._disconnect()
                break

            if not chunk:
                self._disconnect()
                break

            self._buffer += chunk.decode(
                "utf-8",
                errors="ignore",
            )

            self._consume_buffer()

    def _connect_if_due(self) -> None:
        now = time.monotonic()

        if (
            now - self._last_connect_attempt
            < self.reconnect_seconds
        ):
            return

        self._last_connect_attempt = now

        try:
            gps_socket = socket.create_connection(
                (self.host, self.port),
                timeout=0.25,
            )
            gps_socket.sendall(
                b'?WATCH={"enable":true,"json":true};\n'
            )
            gps_socket.setblocking(False)
        except (ConnectionError, OSError):
            self._connected = False
            return

        self._socket = gps_socket
        self._buffer = ""
        self._connected = True

    def _consume_buffer(self) -> None:
        while "\n" in self._buffer:
            line, self._buffer = self._buffer.split(
                "\n",
                1,
            )

            line = line.strip()

            if not line:
                continue

            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue

            if isinstance(message, dict):
                self._handle_message(message)

    def _handle_message(
        self,
        message: dict[str, Any],
    ) -> None:
        if message.get("class") != "TPV":
            return

        mode = self._integer(message.get("mode")) or 1
        self._last_mode = mode

        if mode < 2:
            return

        latitude = self._number(message.get("lat"))
        longitude = self._number(message.get("lon"))

        if latitude is None or longitude is None:
            return

        self._last_good_position = Position(
            latitude=latitude,
            longitude=longitude,
        )
        self._last_fix_monotonic = time.monotonic()

    def _disconnect(self) -> None:
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass

        self._socket = None
        self._buffer = ""
        self._connected = False

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, (int, float)):
            return float(value)

        return None

    @staticmethod
    def _integer(value: Any) -> int | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value

        if isinstance(value, float) and value.is_integer():
            return int(value)

        return None