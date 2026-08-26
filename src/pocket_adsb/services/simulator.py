import random

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.models.receiver_status import ReceiverStatus
from pocket_adsb.services.data_source import AircraftDataSource


class AircraftSimulator(AircraftDataSource):
    def __init__(self) -> None:
        self.aircraft = [
            Aircraft(
                "406B90",
                "BAW143",
                "G-XWBA",
                "A35K",
                "A5",
                "United Kingdom",
                "British Airways",
                "British Airways",
                34000,
                36000,
                456,
                1200,
                "5162",
                22.4,
                128,
                94,
                "LHR",
                "DEL",
                0.2,
                0.4,
            ),
            Aircraft(
                "4CA123",
                "RYR82QP",
                "EI-DCL",
                "B738",
                "A3",
                "Ireland",
                "Ryanair",
                "Ryanair",
                12400,
                14000,
                287,
                1800,
                "4721",
                9.7,
                241,
                218,
                "BHX",
                "DUB",
                1.4,
                2.1,
            ),
            Aircraft(
                "406A12",
                "EZY51CD",
                "G-EZTH",
                "A320",
                "A3",
                "United Kingdom",
                "easyJet",
                "easyJet",
                7200,
                9000,
                231,
                -900,
                "3614",
                6.1,
                35,
                352,
                "BRS",
                "EDI",
                0.7,
                1.2,
            ),
            Aircraft(
                "407123",
                "VIR107",
                "G-VLUX",
                "A35K",
                "A5",
                "United Kingdom",
                "Virgin Atlantic",
                "Virgin Atlantic",
                29800,
                32000,
                472,
                1500,
                "2246",
                31.8,
                163,
                147,
                "LHR",
                "ATL",
                2.3,
                3.6,
            ),
            Aircraft(
                "400ABC",
                "TOM4GX",
                "G-TUMJ",
                "B38M",
                "A3",
                "United Kingdom",
                "TUI Airways",
                "TUI Airways",
                18300,
                20000,
                334,
                -1100,
                "6031",
                17.2,
                292,
                184,
                "MAN",
                "TFS",
                0.5,
                0.9,
            ),
            Aircraft(
                "4D2211",
                "WZZ31A",
                "9H-WDK",
                "A321",
                "A3",
                "Malta",
                "Wizz Air",
                "Wizz Air Malta",
                27000,
                29000,
                421,
                700,
                "1743",
                38.5,
                74,
                81,
                "LTN",
                "KRK",
                4.2,
                6.8,
            ),
        ]

        self.message_rate = 0

    def get_aircraft(self) -> list[Aircraft]:
        for aircraft in self.aircraft:
            aircraft.distance_nm = max(
                0.1,
                aircraft.distance_nm + random.uniform(-0.3, 0.3),
            )

            aircraft.bearing_from_us_deg = (
                aircraft.bearing_from_us_deg + random.randint(-2, 2)
            ) % 360

            aircraft.track_deg = (
                aircraft.track_deg + random.randint(-1, 1)
            ) % 360

            aircraft.altitude_ft = max(
                0,
                aircraft.altitude_ft
                + random.choice([-100, 0, 0, 0, 100]),
            )

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
            else:
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