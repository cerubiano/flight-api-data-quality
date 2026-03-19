"""Port definitions for external flight providers.

This module declares the FlightProviderPort interface used by all provider
adapters (Amadeus, Duffel, etc.).
"""

# 1. Standard library
from abc import ABC, abstractmethod

# 3. Internal — absolute imports only
from src.domain.models.flight_model import FlightModel


class FlightProviderPort(ABC):
    """Contract for any external flight search provider adapter.

    Implementations must return a list of normalized `FlightModel` objects so
    the domain can validate and score flights without knowing provider-specific
    schemas.
    """

    @abstractmethod
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
    ) -> list[FlightModel]:
        """Search flights and return normalized FlightModel list.

        Args:
            origin: IATA origin airport code (3 characters).
            destination: IATA destination airport code (3 characters).
            departure_date: Departure date (provider-accepted date string).
            adults: Number of adult passengers.

        Returns:
            List of normalized `FlightModel` offers.
        """
