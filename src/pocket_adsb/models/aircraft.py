from dataclasses import dataclass


@dataclass
class Aircraft:
    icao: str
    callsign: str = ""
    registration: str = ""
    aircraft_type: str = ""
    description: str = ""
    category: str = ""
    country: str = ""
    airline: str = ""
    airline_callsign: str = ""
    operator: str = ""

    altitude_ft: int | None = None
    selected_altitude_ft: int | None = None
    speed_kt: float | None = None
    vertical_rate_fpm: int | None = None
    squawk: str = ""

    latitude: float | None = None
    longitude: float | None = None

    distance_nm: float | None = None
    bearing_from_us_deg: float | None = None
    track_deg: float | None = None

    origin: str = ""
    destination: str = ""

    seen_seconds: float = 0.0
    seen_pos_seconds: float | None = None