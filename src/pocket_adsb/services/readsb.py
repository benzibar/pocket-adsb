import json
from pathlib import Path

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
        self.aircraft_json_path = Path(aircraft_json_path)
        self.position_source = position_source

        self.aircraft: list[Aircraft] = []
        self.message_count = 0

    def get_aircraft(self) -> list[Aircraft]:
        with self.aircraft_json_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        self.message_count = int(data.get("messages", 0))

        aircraft_list: list[Aircraft] = []

        own_position = (
            self.position_source.get_position()
            if self.position_source is not None
            else None
        )

        for raw in data.get("aircraft", []):
            icao = str(raw.get("hex", "")).upper()

            if not icao:
                continue

            callsign = str(raw.get("flight", "")).strip()

            altitude = raw.get("alt_baro")
            if not isinstance(altitude, (int, float)):
                altitude = None

            selected_altitude = raw.get("nav_altitude_mcp")
            if not isinstance(selected_altitude, (int, float)):
                selected_altitude = None

            speed = raw.get("gs")
            if not isinstance(speed, (int, float)):
                speed = None

            vertical_rate = raw.get("baro_rate")
            if not isinstance(vertical_rate, (int, float)):
                vertical_rate = None

            track = raw.get("track")
            if not isinstance(track, (int, float)):
                track = None

            latitude = raw.get("lat")
            if not isinstance(latitude, (int, float)):
                latitude = None

            longitude = raw.get("lon")
            if not isinstance(longitude, (int, float)):
                longitude = None

            seen = raw.get("seen")
            if not isinstance(seen, (int, float)):
                seen = 0.0

            seen_pos = raw.get("seen_pos")
            if not isinstance(seen_pos, (int, float)):
                seen_pos = None

            distance_nm = None
            bearing_from_us_deg = None

            if (
                own_position is not None
                and latitude is not None
                and longitude is not None
            ):
                distance_nm = calculate_distance_nm(
                    own_position,
                    float(latitude),
                    float(longitude),
                )

                bearing_from_us_deg = calculate_bearing_deg(
                    own_position,
                    float(latitude),
                    float(longitude),
                )

            aircraft_list.append(
                Aircraft(
                    icao=icao,
                    callsign=callsign,
                    category=str(raw.get("category", "")),
                    altitude_ft=(
                        int(altitude)
                        if altitude is not None
                        else None
                    ),
                    selected_altitude_ft=(
                        int(selected_altitude)
                        if selected_altitude is not None
                        else None
                    ),
                    speed_kt=(
                        float(speed)
                        if speed is not None
                        else None
                    ),
                    vertical_rate_fpm=(
                        int(vertical_rate)
                        if vertical_rate is not None
                        else None
                    ),
                    squawk=str(raw.get("squawk", "")),
                    latitude=(
                        float(latitude)
                        if latitude is not None
                        else None
                    ),
                    longitude=(
                        float(longitude)
                        if longitude is not None
                        else None
                    ),
                    distance_nm=distance_nm,
                    bearing_from_us_deg=bearing_from_us_deg,
                    track_deg=(
                        float(track)
                        if track is not None
                        else None
                    ),
                    seen_seconds=float(seen),
                    seen_pos_seconds=(
                        float(seen_pos)
                        if seen_pos is not None
                        else None
                    ),
                )
            )

        self.aircraft = aircraft_list

        return self.aircraft

    def get_status(self) -> ReceiverStatus:
        gps_status = (
            "FIX"
            if (
                self.position_source is not None
                and self.position_source.get_position() is not None
            )
            else "---"
        )

        return ReceiverStatus(
            mode="ADSB",
            aircraft_count=len(self.aircraft),
            message_rate=0,
            gps_status=gps_status,
            wifi_status="---",
        )