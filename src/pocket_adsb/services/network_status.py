import platform
import subprocess
import time
from pathlib import Path


class NetworkStatusService:
    def __init__(
        self,
        cache_seconds: float = 5.0,
    ) -> None:
        self.cache_seconds = cache_seconds
        self._last_check = 0.0
        self._last_status = False

    def is_wifi_connected(self) -> bool:
        now = time.monotonic()

        if (
            now - self._last_check
            < self.cache_seconds
        ):
            return self._last_status

        self._last_status = (
            self._check_wifi()
        )
        self._last_check = now

        return self._last_status

    def status_text(self) -> str:
        return (
            "ON"
            if self.is_wifi_connected()
            else "OFF"
        )

    def _check_wifi(self) -> bool:
        system = platform.system()

        if system == "Windows":
            return self._check_windows()

        if system == "Linux":
            return self._check_linux()

        return False

    @staticmethod
    def _check_windows() -> bool:
        try:
            result = subprocess.run(
                [
                    "netsh",
                    "wlan",
                    "show",
                    "interfaces",
                ],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return False

        output = result.stdout.lower()

        return (
            "state" in output
            and "connected" in output
            and "disconnected" not in output
        )

    @staticmethod
    def _check_linux() -> bool:
        wireless_path = Path(
            "/sys/class/net"
        )

        if wireless_path.exists():
            for interface in wireless_path.iterdir():
                if not (
                    interface.name.startswith("wlan")
                    or interface.name.startswith("wl")
                ):
                    continue

                operstate = (
                    interface / "operstate"
                )

                try:
                    state = (
                        operstate
                        .read_text(
                            encoding="utf-8"
                        )
                        .strip()
                        .lower()
                    )
                except OSError:
                    continue

                if state == "up":
                    return True

        return False