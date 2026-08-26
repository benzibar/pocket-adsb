from abc import ABC, abstractmethod

from pocket_adsb.models.position import Position


class PositionSource(ABC):
    @abstractmethod
    def get_position(self) -> Position | None:
        """Return our current position, or None if unavailable."""
        pass


class FixedPositionSource(PositionSource):
    def __init__(self, latitude: float, longitude: float) -> None:
        self.position = Position(
            latitude=latitude,
            longitude=longitude,
        )

    def get_position(self) -> Position:
        return self.position