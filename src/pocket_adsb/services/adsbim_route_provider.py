import json
import urllib.error
import urllib.request

from pocket_adsb.services.route_provider import (
    RouteProvider,
    RouteResult,
)


class AdsbImRouteProvider(RouteProvider):
    URL = "https://adsb.im/api/0/routeset"

    def lookup(
        self,
        flight_id: str,
    ) -> RouteResult | None:
        callsign = flight_id.strip().upper()

        if not callsign:
            return None

        payload = {
            "planes": [
                {
                    "callsign": callsign,
                    "lat": 0.0,
                    "lng": 0.0,
                }
            ]
        }

        body = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.URL,
            data=body,
            method="POST",
            headers={
                "User-Agent": "Pocket-ADS-B/0.1",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=5,
            ) as response:
                data = json.load(response)

        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            json.JSONDecodeError,
        ):
            return None

        if not isinstance(data, list) or not data:
            return None

        route = data[0]

        if not isinstance(route, dict):
            return None

        iata_codes = route.get(
            "_airport_codes_iata"
        )

        if (
            isinstance(iata_codes, str)
            and "-" in iata_codes
        ):
            origin, destination = (
                iata_codes.split("-", 1)
            )

            if origin and destination:
                return RouteResult(
                    origin=origin.upper(),
                    destination=destination.upper(),
                    source="adsbim",
                )

        airports = route.get("_airports")

        if (
            not isinstance(airports, list)
            or len(airports) < 2
        ):
            return None

        origin = airports[0]
        destination = airports[1]

        if (
            not isinstance(origin, dict)
            or not isinstance(destination, dict)
        ):
            return None

        origin_code = (
            origin.get("iata")
            or origin.get("icao")
            or ""
        )

        destination_code = (
            destination.get("iata")
            or destination.get("icao")
            or ""
        )

        if not origin_code or not destination_code:
            return None

        return RouteResult(
            origin=str(origin_code).upper(),
            destination=str(destination_code).upper(),
            source="adsbim",
        )