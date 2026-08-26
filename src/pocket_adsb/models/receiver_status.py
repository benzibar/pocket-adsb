from dataclasses import dataclass


@dataclass
class ReceiverStatus:
    mode: str
    aircraft_count: int
    message_rate: float
    gps_status: str
    wifi_status: str