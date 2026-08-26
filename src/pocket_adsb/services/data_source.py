from abc import ABC, abstractmethod

from pocket_adsb.models.aircraft import Aircraft
from pocket_adsb.models.receiver_status import ReceiverStatus


class AircraftDataSource(ABC):
    @abstractmethod
    def get_aircraft(self) -> list[Aircraft]:
        """Return the currently known aircraft."""
        pass

    @abstractmethod
    def get_status(self) -> ReceiverStatus:
        """Return current receiver status."""
        pass