import random

from pocket_adsb.models.aircraft import Aircraft


class AircraftSimulator:
    def __init__(self) -> None:
        self.aircraft = [
            Aircraft(
                "406B90", "BAW143", "G-XWBA", "A35K",
                34000, 456, 22.4, 128, 94, "LHR", "DEL"
            ),
            Aircraft(
                "4CA123", "RYR82QP", "EI-DCL", "B738",
                12400, 287, 9.7, 241, 218, "BHX", "DUB"
            ),
            Aircraft(
                "406A12", "EZY51CD", "G-EZTH", "A320",
                7200, 231, 6.1, 35, 352, "BRS", "EDI"
            ),
            Aircraft(
                "407123", "VIR107", "G-VLUX", "A35K",
                29800, 472, 31.8, 163, 147, "LHR", "ATL"
            ),
            Aircraft(
                "400ABC", "TOM4GX", "G-TUMJ", "B38M",
                18300, 334, 17.2, 292, 184, "MAN", "TFS"
            ),
            Aircraft(
                "4D2211", "WZZ31A", "9H-WDK", "A321",
                27000, 421, 38.5, 74, 81, "LTN", "KRK"
            ),
        ]

    def update(self) -> list[Aircraft]:
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
                aircraft.altitude_ft + random.choice([-100, 0, 0, 0, 100]),
            )

        return self.aircraft