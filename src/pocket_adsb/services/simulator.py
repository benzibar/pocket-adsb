import random

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.models.receiver_status import ReceiverStatus
from pocket_adsb.services.data_source import AircraftDataSource


class AircraftSimulator(AircraftDataSource):
    def __init__(self) -> None:
        self.aircraft = [
            Aircraft(
                icao="406B90",
                callsign="BAW143",
                registration="G-XWBA",
                aircraft_type="A35K",
                category="A5",
                country="United Kingdom",
                airline="British Airways",
                operator="British Airways",
                altitude_ft=34000,
                selected_altitude_ft=36000,
                speed_kt=456,
                vertical_rate_fpm=1200,
                squawk="5162",
                latitude=52.0500,
                longitude=-2.1000,
                distance_nm=22.4,
                bearing_from_us_deg=128,
                track_deg=94,
                origin="LHR",
                destination="DEL",
                seen_seconds=0.2,
                seen_pos_seconds=0.4,
            ),
            Aircraft(
                icao="4CA123",
                callsign="RYR82QP",
                registration="EI-DCL",
                aircraft_type="B738",
                category="A3",
                country="Ireland",
                airline="Ryanair",
                operator="Ryanair",
                altitude_ft=12400,
                selected_altitude_ft=14000,
                speed_kt=287,
                vertical_rate_fpm=1800,
                squawk="4721",
                latitude=52.1000,
                longitude=-2.3000,
                distance_nm=9.7,
                bearing_from_us_deg=241,
                track_deg=218,
                origin="BHX",
                destination="DUB",
                seen_seconds=1.4,
                seen_pos_seconds=2.1,
            ),
            Aircraft(
                icao="406A12",
                callsign="EZY51CD",
                registration="G-EZTH",
                aircraft_type="A320",
                category="A3",
                country="United Kingdom",
                airline="easyJet",
                operator="easyJet",
                altitude_ft=7200,
                selected_altitude_ft=9000,
                speed_kt=231,
                vertical_rate_fpm=-900,
                squawk="3614",
                latitude=52.0200,
                longitude=-2.0500,
                distance_nm=6.1,
                bearing_from_us_deg=35,
                track_deg=352,
                origin="BRS",
                destination="EDI",
                seen_seconds=0.7,
                seen_pos_seconds=1.2,
            ),
            Aircraft(
                icao="407123",
                callsign="VIR107",
                registration="G-VLUX",
                aircraft_type="A35K",
                category="A5",
                country="United Kingdom",
                airline="Virgin Atlantic",
                operator="Virgin Atlantic",
                altitude_ft=29800,
                selected_altitude_ft=32000,
                speed_kt=472,
                vertical_rate_fpm=1500,
                squawk="2246",
                latitude=52.2500,
                longitude=-2.4000,
                distance_nm=31.8,
                bearing_from_us_deg=163,
                track_deg=147,
                origin="LHR",
                destination="ATL",
                seen_seconds=2.3,
                seen_pos_seconds=3.6,
            ),
            Aircraft(
                icao="400ABC",
                callsign="TOM4GX",
                registration="G-TUMJ",
                aircraft_type="B38M",
                category="A3",
                country="United Kingdom",
                airline="TUI Airways",
                operator="TUI Airways",
                altitude_ft=18300,
                selected_altitude_ft=20000,
                speed_kt=334,
                vertical_rate_fpm=-1100,
                squawk="6031",
                latitude=52.1800,
                longitude=-2.2000,
                distance_nm=17.2,
                bearing_from_us_deg=292,
                track_deg=184,
                origin="MAN",
                destination="TFS",
                seen_seconds=0.5,
                seen_pos_seconds=0.9,
            ),
            Aircraft(
                icao="4D2211",
                callsign="WZZ31A",
                registration="9H-WDK",
                aircraft_type="A321",
                category="A3",
                country="Malta",
                airline="Wizz Air",
                operator="Wizz Air Malta",
                altitude_ft=27000,
                selected_altitude_ft=29000,
                speed_kt=421,
                vertical_rate_fpm=700,
                squawk="1743",
                latitude=52.3000,
                longitude=-1.9500,
                distance_nm=38.5,
                bearing_from_us_deg=74,
                track_deg=81,
                origin="LTN",
                destination="KRK",
                seen_seconds=4.2,
                seen_pos_seconds=6.8,
            ),
        ]

        self.message_rate = 0

    def get_aircraft(self) -> list[Aircraft]:
        for aircraft in self.aircraft:
            if aircraft.distance_nm is not None:
                aircraft.distance_nm = max(
                    0.1,
                    aircraft.distance_nm + random.uniform(-0.3, 0.3),
                )

            if aircraft.bearing_from_us_deg is not None:
                aircraft.bearing_from_us_deg = (
                    aircraft.bearing_from_us_deg
                    + random.randint(-2, 2)
                ) % 360

            if aircraft.track_deg is not None:
                aircraft.track_deg = (
                    aircraft.track_deg
                    + random.randint(-1, 1)
                ) % 360

            if aircraft.altitude_ft is not None:
                aircraft.altitude_ft = max(
                    0,
                    aircraft.altitude_ft
                    + random.choice([-100, 0, 0, 0, 100]),
                )

            if aircraft.vertical_rate_fpm is not None:
                aircraft.vertical_rate_fpm = max(
                    -5000,
                    min(
                        5000,
                        aircraft.vertical_rate_fpm
                        + random.choice([-100, 0, 0, 0, 100]),
                    ),
                )

            if random.random() < 0.80:
                aircraft.seen_seconds = random.uniform(0.0, 0.9)
            else:
                aircraft.seen_seconds += 1.0

            if random.random() < 0.60:
                aircraft.seen_pos_seconds = random.uniform(0.0, 1.0)
            elif aircraft.seen_pos_seconds is not None:
                aircraft.seen_pos_seconds += 1.0

        self.message_rate = random.randint(35, 80)

        return self.aircraft

    def get_status(self) -> ReceiverStatus:
        return ReceiverStatus(
            mode="SIM",
            aircraft_count=len(self.aircraft),
            message_rate=self.message_rate,
            gps_status="SIM",
            wifi_status="ONLINE",
        )