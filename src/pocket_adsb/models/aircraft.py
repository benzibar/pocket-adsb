from dataclasses import dataclass


@dataclass
class Aircraft:
    icao: str
    callsign: str
    registration: str
    aircraft_type: str
    altitude_ft: int
    speed_kt: int
    distance_nm: float
    bearing_from_us_deg: int
    track_deg: int
    origin: str
    destination: str