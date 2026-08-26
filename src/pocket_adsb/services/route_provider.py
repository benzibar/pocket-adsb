from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteResult:
    origin: str
    destination: str
    source: str


class RouteProvider(ABC):
    @abstractmethod
    def lookup(
        self,
        flight_id: str,
    ) -> RouteResult | None:
        pass