"""Amadeus flight provider adapter.

Implements `FlightProviderPort` for Amadeus GDS Flight Offers Search.
"""

# 1. Standard library
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

# 2. Third-party
import requests

# 3. Internal — absolute imports only
from src.domain.exceptions import AdapterError
from src.domain.models.flight_model import FlightModel
from src.domain.ports.provider_port import FlightProviderPort

AMADEUS_BASE_URL = "https://test.api.amadeus.com"
OAUTH2_TOKEN_URL = f"{AMADEUS_BASE_URL}/v1/security/oauth2/token"
FLIGHT_OFFERS_URL = f"{AMADEUS_BASE_URL}/v2/shopping/flight-offers"

GRANT_TYPE_CLIENT_CREDENTIALS = "client_credentials"
DEFAULT_TIMEOUT_SECONDS = 30
MAX_FLIGHT_OFFERS = 5

SOURCE_AMADEUS = "amadeus"

PRICE_FEES_KEY = "fees"
PRICE_TOTAL_KEY = "grandTotal"
PRICE_BASE_KEY = "base"
PRICE_CURRENCY_KEY = "currency"


class AmadeusAdapter(FlightProviderPort):
    """Amadeus implementation of `FlightProviderPort`."""

    def __init__(self, amadeus_api_key: str, amadeus_api_secret: str) -> None:
        """Create a new Amadeus adapter.

        Args:
            amadeus_api_key: Amadeus API key (client_id).
            amadeus_api_secret: Amadeus API secret (client_secret).
        """

        self._api_key = amadeus_api_key
        self._api_secret = amadeus_api_secret

    def _get_token(self) -> str:
        """Authenticate with Amadeus and return an OAuth2 bearer token.

        Returns:
            OAuth2 access token string.

        Raises:
            AdapterError: If authentication fails or the response is invalid.
        """

        data = {
            "grant_type": GRANT_TYPE_CLIENT_CREDENTIALS,
            "client_id": self._api_key,
            "client_secret": self._api_secret,
        }

        try:
            response = requests.post(OAUTH2_TOKEN_URL, data=data, timeout=DEFAULT_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as e:
            raise AdapterError(f"Amadeus OAuth2 token request failed: {e}") from e
        except ValueError as e:
            raise AdapterError(f"Amadeus OAuth2 token response was not valid JSON: {e}") from e

        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise AdapterError("Amadeus OAuth2 token response missing access_token")

        return token

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
            departure_date: Departure date (YYYY-MM-DD).
            adults: Number of adult passengers.

        Returns:
            List of normalized `FlightModel` offers.

        Raises:
            AdapterError: If the API call fails or the payload cannot be parsed.
        """

        token = self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": MAX_FLIGHT_OFFERS,
        }

        try:
            response = requests.get(
                FLIGHT_OFFERS_URL,
                headers=headers,
                params=params,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as e:
            raise AdapterError(f"Amadeus flight offers request failed: {e}") from e
        except ValueError as e:
            raise AdapterError(f"Amadeus flight offers response was not valid JSON: {e}") from e

        offers = payload.get("data")
        if offers is None:
            return []
        if not isinstance(offers, list):
            raise AdapterError("Amadeus flight offers response missing data list")

        flights: list[FlightModel] = []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            flights.append(self._map_offer_to_flight_model(offer))

        return flights

    def _map_offer_to_flight_model(self, offer: dict[str, Any]) -> FlightModel:
        """Map a single Amadeus offer payload to `FlightModel`.

        Mapping is based on the SPEC-002 Silver schema data dictionary.

        Args:
            offer: A single offer dict from Amadeus `flight-offers` response.

        Returns:
            Normalized `FlightModel`.

        Raises:
            AdapterError: If required fields are missing or malformed.
        """

        itinerary = self._first_dict(offer.get("itineraries"))
        segment = self._first_dict((itinerary or {}).get("segments"))
        departure = (segment or {}).get("departure") if isinstance((segment or {}).get("departure"), dict) else None
        arrival = (segment or {}).get("arrival") if isinstance((segment or {}).get("arrival"), dict) else None

        carrier_code = (segment or {}).get("carrierCode")
        flight_number = (segment or {}).get("number")
        departure_at = (departure or {}).get("at")
        arrival_at = (arrival or {}).get("at")
        duration = (itinerary or {}).get("duration")
        origin_iata = (departure or {}).get("iataCode")
        destination_iata = (arrival or {}).get("iataCode")

        price = offer.get("price") if isinstance(offer.get("price"), dict) else {}
        base_amount = self._to_decimal(price.get(PRICE_BASE_KEY))
        total_amount = self._to_decimal(price.get(PRICE_TOTAL_KEY))
        currency = price.get(PRICE_CURRENCY_KEY)
        tax_amount = self._sum_fees(price.get(PRICE_FEES_KEY))

        fare_details = self._first_fare_details(offer)
        cabin_class = fare_details.get("cabin") if fare_details else None
        fare_basis = fare_details.get("fareBasis") if fare_details else None
        fare_brand = fare_details.get("brandedFare") if fare_details else None

        included_checked_bags = fare_details.get("includedCheckedBags") if fare_details else None
        checked_bags = self._get_quantity(included_checked_bags)

        included_cabin_bags = fare_details.get("includedCabinBags") if fare_details else None
        carry_on_bags = self._get_quantity(included_cabin_bags)

        try:
            return FlightModel(
                source=SOURCE_AMADEUS,
                carrier_code=carrier_code,
                flight_number=flight_number,
                origin_iata=origin_iata,
                destination_iata=destination_iata,
                departure_at=departure_at,
                arrival_at=arrival_at,
                total_amount=total_amount,
                currency=currency,
                base_amount=base_amount,
                tax_amount=tax_amount,
                duration=duration,
                cabin_class=cabin_class,
                fare_basis=fare_basis,
                fare_brand=fare_brand,
                checked_bags=checked_bags,
                carry_on_bags=carry_on_bags,
                refund_allowed=None,
                change_allowed=None,
            )
        except Exception as e:
            raise AdapterError(f"Failed to normalize Amadeus offer into FlightModel: {e}") from e

    def _sum_fees(self, fees: Any) -> Decimal | None:
        if not isinstance(fees, list) or not fees:
            return None

        total = Decimal("0")
        for fee in fees:
            if not isinstance(fee, dict):
                continue
            amount = self._to_decimal(fee.get("amount"))
            if amount is None:
                continue
            total += amount
        return total

    def _to_decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _get_quantity(self, maybe_quantity_obj: Any) -> int | None:
        if not isinstance(maybe_quantity_obj, dict):
            return None
        quantity = maybe_quantity_obj.get("quantity")
        if isinstance(quantity, int):
            return quantity
        return None

    def _first_dict(self, maybe_list: Any) -> dict[str, Any] | None:
        if not isinstance(maybe_list, list) or not maybe_list:
            return None
        first = maybe_list[0]
        if isinstance(first, dict):
            return first
        return None

    def _first_fare_details(self, offer: dict[str, Any]) -> dict[str, Any] | None:
        traveler_pricing = self._first_dict(offer.get("travelerPricings"))
        fare_details_list = (traveler_pricing or {}).get("fareDetailsBySegment")
        return self._first_dict(fare_details_list)
