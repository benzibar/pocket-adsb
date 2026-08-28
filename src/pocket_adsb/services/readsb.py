from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.models.receiver_status import ReceiverStatus
from pocket_adsb.services.data_source import AircraftDataSource
from pocket_adsb.services.position_source import PositionSource
from pocket_adsb.utils.geography import (
    calculate_bearing_deg,
    calculate_distance_nm,
)


class ReadsbDataSource(AircraftDataSource):
    def __init__(
        self,
        aircraft_json_path: str | Path,
        position_source: PositionSource | None = None,
    ) -> None:
        self.aircraft_json_path = Path(
            aircraft_json_path
        )

        self.position_source = position_source

        self._last_aircraft: list[Aircraft] = []
        self._last_message_count: int | None = None
        self._last_now: float | None = None
        self._message_rate = 0.0

    def get_aircraft(self) -> list[Aircraft]:
        data = self._read_json()

        if data is None:
            return self._last_aircraft

        aircraft_data = data.get(
            "aircraft",
            [],
        )

        aircraft_list: list[Aircraft] = []

        receiver_position = None

        if self.position_source is not None:
            receiver_position = (
                self.position_source.get_position()
            )

        for raw in aircraft_data:
            if not isinstance(raw, dict):
                continue

            aircraft = self._parse_aircraft(
                raw
            )

            if aircraft is None:
                continue

            if (
                receiver_position is not None
                and aircraft.latitude is not None
                and aircraft.longitude is not None
            ):
                aircraft.distance_nm = (
                    calculate_distance_nm(
                        receiver_position,
                        aircraft.latitude,
                        aircraft.longitude,
                    )
                )

                aircraft.bearing_from_us_deg = (
                    calculate_bearing_deg(
                        receiver_position,
                        aircraft.latitude,
                        aircraft.longitude,
                    )
                )

            aircraft_list.append(
                aircraft
            )

        self._update_message_rate(
            data
        )

        self._last_aircraft = aircraft_list

        return aircraft_list

    def get_status(self) -> ReceiverStatus:
        position_status = "---"

        if self.position_source is not None:
            position_status = (
                self.position_source.status_text()
            )

        return ReceiverStatus(
            mode="READSB",
            aircraft_count=len(
                self._last_aircraft
            ),
            message_rate=self._message_rate,
            gps_status=position_status,
            wifi_status="---",
        )

    def _read_json(
        self,
    ) -> dict[str, Any] | None:
        try:
            with self.aircraft_json_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

        except (
            FileNotFoundError,
            PermissionError,
            json.JSONDecodeError,
            OSError,
        ):
            return None

        if not isinstance(data, dict):
            return None

        return data

    def _parse_aircraft(
        self,
        raw: dict[str, Any],
    ) -> Aircraft | None:
        icao = self._text(
            raw.get("hex")
        ).upper()

        if not icao:
            return None

        latitude = self._number(
            raw.get("lat")
        )

        longitude = self._number(
            raw.get("lon")
        )

        altitude = self._integer(
            raw.get("alt_baro")
        )

        if altitude is None:
            altitude = self._integer(
                raw.get("alt_geom")
            )

        selected_altitude = self._integer(
            raw.get("nav_altitude_mcp")
        )

        if selected_altitude is None:
            selected_altitude = self._integer(
                raw.get("nav_altitude_fms")
            )

        speed = self._number(
            raw.get("gs")
        )

        track = self._number(
            raw.get("track")
        )

        vertical_rate = self._integer(
            raw.get("baro_rate")
        )

        if vertical_rate is None:
            vertical_rate = self._integer(
                raw.get("geom_rate")
            )

        seen = self._number(
            raw.get("seen")
        )

        if seen is None:
            seen = 0.0

        seen_pos = self._number(
            raw.get("seen_pos")
        )

        db_flags = self._integer(
            raw.get("dbFlags")
        )

        is_military = bool(
            (db_flags or 0) & 1
        )

        return Aircraft(
            icao=icao,
            callsign=self._text(
                raw.get("flight")
            ),
            registration=self._text(
                raw.get("r")
            ),
            aircraft_type=self._text(
                raw.get("t")
            ),
            category=self._text(
                raw.get("category")
            ),
            squawk=self._text(
                raw.get("squawk")
            ),
            is_military=is_military,
            altitude_ft=altitude,
            selected_altitude_ft=selected_altitude,
            speed_kt=speed,
            vertical_rate_fpm=vertical_rate,
            latitude=latitude,
            longitude=longitude,
            track_deg=track,
            seen_seconds=seen,
            seen_pos_seconds=seen_pos,
        )

    def _update_message_rate(
        self,
        data: dict[str, Any],
    ) -> None:
        message_count = self._integer(
            data.get("messages")
        )

        now = self._number(
            data.get("now")
        )

        if (
            message_count is None
            or now is None
        ):
            return

        if (
            self._last_message_count is not None
            and self._last_now is not None
        ):
            elapsed = (
                now - self._last_now
            )

            message_delta = (
                message_count
                - self._last_message_count
            )

            if (
                elapsed > 0
                and message_delta >= 0
            ):
                self._message_rate = (
                    message_delta / elapsed
                )

        self._last_message_count = (
            message_count
        )

        self._last_now = now

    @staticmethod
    def _text(
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return str(value).strip()

    @staticmethod
    def _number(
        value: Any,
    ) -> float | None:
        if value is None:
            return None

        try:
            return float(value)

        except (
            TypeError,
            ValueError,
        ):
            return None

    @staticmethod
    def _integer(
        value: Any,
    ) -> int | None:
        if value is None:
            return None

        try:
            return int(
                float(value)
            )

        except (
            TypeError,
            ValueError,
        ):
            return None
