import json
import urllib.error
import urllib.parse
import urllib.request

from pocket_adsb.services.route_provider import (
    RouteProvider,
    RouteResult,
)


class AdsbDbRouteProvider(RouteProvider):
    BASE_URL = "https://api.adsbdb.com/v0/callsign"

    def lookup(
        self,
        flight_id: str,
    ) -> RouteResult | None:
        flight_id = flight_id.strip().upper()

        if not flight_id:
            return None

        encoded_callsign = urllib.parse.quote(
            flight_id,
            safe="",
        )

        url = (
            f"{self.BASE_URL}/"
            f"{encoded_callsign}"
        )

        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Pocket-ADS-B/0.1",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=5,
            ) as response:
                data = json.load(response)

        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None

            raise

        route = (
            data
            .get("response", {})
            .get("flightroute")
        )

        if not route:
            return None

        origin = route.get("origin") or {}
        destination = (
            route.get("destination") or {}
        )

        origin_code = (
            origin.get("iata_code")
            or origin.get("icao_code")
            or ""
        )

        destination_code = (
            destination.get("iata_code")
            or destination.get("icao_code")
            or ""
        )

        if not origin_code or not destination_code:
            return None

        return RouteResult(
            origin=origin_code.upper(),
            destination=destination_code.upper(),
            source="adsbdb",
        )