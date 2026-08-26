from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from pocket_adsb.services.route_cache import (
    Route,
    RouteCache,
)
from pocket_adsb.services.route_provider import (
    RouteProvider,
)


class RouteService:
    def __init__(
        self,
        cache: RouteCache,
        provider: RouteProvider | None = None,
    ) -> None:
        self.cache = cache
        self.provider = provider

        # Keep the worker count deliberately small.
        # Route enrichment is supplementary and should
        # never dominate Pocket ADS-B's resources.
        self.executor = ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="route-lookup",
        )

        # Tracks callsigns currently being looked up so
        # repeated UI refreshes don't queue duplicates.
        self._in_flight: set[str] = set()
        self._lock = Lock()

    def lookup(
        self,
        flight_id: str,
    ) -> Route | None:
        """
        Return a cached route immediately if available.

        If no cached route exists, queue an online lookup
        in the background and return None immediately.
        """
        normalised = self.cache.normalise_flight_id(
            flight_id
        )

        if not normalised:
            return None

        cached = self.cache.lookup(
            normalised
        )

        if cached is not None:
            return cached

        if self.cache.has_recent_negative(
            normalised
        ):
            return None

        if self.provider is None:
            return None

        self._queue_lookup(
            normalised
        )

        return None

    def _queue_lookup(
        self,
        flight_id: str,
    ) -> None:
        with self._lock:
            if flight_id in self._in_flight:
                return

            self._in_flight.add(
                flight_id
            )

        self.executor.submit(
            self._background_lookup,
            flight_id,
        )

    def _background_lookup(
        self,
        flight_id: str,
    ) -> None:
        try:
            if self.provider is None:
                return

            try:
                result = self.provider.lookup(
                    flight_id
                )
            except Exception:
                # Network/provider failures are not
                # negative-cached. Connectivity may
                # return later.
                return

            if result is None:
                self.cache.store_negative(
                    flight_id=flight_id,
                    source="adsbdb",
                )

                return

            self.cache.store(
                flight_id=flight_id,
                origin=result.origin,
                destination=result.destination,
                source=result.source,
            )

        finally:
            with self._lock:
                self._in_flight.discard(
                    flight_id
                )

    def shutdown(self) -> None:
        self.executor.shutdown(
            wait=False,
            cancel_futures=True,
        )