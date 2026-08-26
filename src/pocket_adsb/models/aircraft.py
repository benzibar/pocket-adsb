from dataclasses import dataclass


@dataclass
class Aircraft:
    icao: str
    callsign: str
    registration: str
    aircraft_type: str
    category: str
    country: str
    airline: str
    operator: str
    altitude_ft: int
    selected_altitude_ft: int | None
    speed_kt: int
    vertical_rate_fpm: int
    squawk: str
    distance_nm: float
    bearing_from_us_deg: int
    track_deg: int
    origin: str
    destination: str
    seen_seconds: float
    seen_pos_seconds: float