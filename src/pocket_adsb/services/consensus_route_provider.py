from pocket_adsb.services.route_provider import (
    RouteProvider,
    RouteResult,
)


class ConsensusRouteProvider(RouteProvider):
    def __init__(
        self,
        providers: list[RouteProvider],
    ) -> None:
        self.providers = providers

    def lookup(
        self,
        flight_id: str,
    ) -> RouteResult | None:
        results: list[RouteResult] = []

        for provider in self.providers:
            try:
                result = provider.lookup(
                    flight_id
                )
            except Exception:
                continue

            if result is not None:
                results.append(result)

        if len(results) < 2:
            return None

        first = results[0]

        for result in results[1:]:
            if (
                result.origin == first.origin
                and result.destination == first.destination
            ):
                return RouteResult(
                    origin=first.origin,
                    destination=first.destination,
                    source="consensus",
                )

        return None