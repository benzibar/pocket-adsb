from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.services.aircraft_database import AircraftDatabase


class AircraftEnricher:
    def __init__(
        self,
        aircraft_database: AircraftDatabase,
    ) -> None:
        self.aircraft_database = aircraft_database

    def enrich(self, aircraft: Aircraft) -> Aircraft:
        info = self.aircraft_database.lookup(
            aircraft.icao
        )

        if info is None:
            return aircraft

        aircraft.registration = info.get(
            "registration",
            "",
        )

        aircraft.aircraft_type = info.get(
            "aircraft_type",
            "",
        )

        aircraft.operator = info.get(
            "operator",
            "",
        )

        return aircraft

    def enrich_all(
        self,
        aircraft_list: list[Aircraft],
    ) -> list[Aircraft]:
        return [
            self.enrich(aircraft)
            for aircraft in aircraft_list
        ]