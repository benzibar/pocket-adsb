from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.services.aircraft_database import AircraftDatabase
from pocket_adsb.services.airline_database import AirlineDatabase
from pocket_adsb.utils.icao_country import country_from_icao
from pocket_adsb.services.route_service import RouteService


class AircraftEnricher:
    def __init__(
        self,
        aircraft_database: AircraftDatabase,
        airline_database: AirlineDatabase,
        route_service: RouteService,
    ) -> None:
        self.aircraft_database = aircraft_database
        self.airline_database = airline_database
        self.route_service = route_service

    def enrich(self, aircraft: Aircraft) -> Aircraft:
        # Aircraft-level enrichment.
        # Never overwrite useful live/readsb data with database values.
        aircraft_info = self.aircraft_database.lookup(
            aircraft.icao
        )

        if aircraft_info is not None:
            if not aircraft.registration:
                aircraft.registration = aircraft_info.get(
                    "registration",
                    "",
                )

            if not aircraft.aircraft_type:
                aircraft.aircraft_type = aircraft_info.get(
                    "aircraft_type",
                    "",
                )

            if not aircraft.description:
                aircraft.description = aircraft_info.get(
                    "description",
                    "",
                )

            if not aircraft.operator:
                aircraft.operator = aircraft_info.get(
                    "operator",
                    "",
                )

        # Country is derived from the ICAO allocation,
        # but only if the live source has not already supplied it.
        if not aircraft.country:
            aircraft.country = country_from_icao(
                aircraft.icao
            )

        # Flight-level airline enrichment.
        airline_code = self._airline_code_from_callsign(
            aircraft.callsign
        )

        if airline_code:
            airline_info = self.airline_database.lookup(
                airline_code
            )

            if airline_info is not None:
                if not aircraft.airline:
                    aircraft.airline = airline_info.get(
                        "name",
                        "",
                    )

                if not aircraft.airline_callsign:
                    aircraft.airline_callsign = airline_info.get(
                        "callsign",
                        "",
                    )

        if (
            aircraft.callsign
            and (
                not aircraft.origin
                or not aircraft.destination
            )
        ):
            route = self.route_service.lookup(
                aircraft.callsign
            )

            if route is not None:
                if not aircraft.origin:
                    aircraft.origin = route.origin

                if not aircraft.destination:
                    aircraft.destination = route.destination

        return aircraft

    def enrich_all(
        self,
        aircraft_list: list[Aircraft],
    ) -> list[Aircraft]:
        return [
            self.enrich(aircraft)
            for aircraft in aircraft_list
        ]

    @staticmethod
    def _airline_code_from_callsign(
        callsign: str,
    ) -> str:
        callsign = callsign.strip().upper()

        if len(callsign) < 3:
            return ""

        prefix = callsign[:3]

        if not prefix.isalpha():
            return ""

        return prefix