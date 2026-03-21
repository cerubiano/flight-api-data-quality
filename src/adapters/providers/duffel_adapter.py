"""Duffel flight provider adapter.

Implements `FlightProviderPort` for Duffel NDC aggregator.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from src.domain.exceptions import AdapterError
from src.domain.models.flight_model import FlightModel
from src.domain.ports.provider_port import FlightProviderPort

DUFFEL_BASE_URL = "https://api.duffel.com"
OFFER_REQUESTS_URL = f"{DUFFEL_BASE_URL}/air/offer_requests"

DUFFEL_VERSION = "v2"
DEFAULT_TIMEOUT_SECONDS = 30
SOURCE_DUFFEL = "duffel"


class DuffelAdapter(FlightProviderPort):
    """Duffel implementation of FlightProviderPort."""

    def __init__(self, access_token: str) -> None:
        """Create a new Duffel adapter.

        Args:
            access_token: Duffel API access token.
        """
        self._access_token = access_token

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
            List of normalized FlightModel offers.

        Raises:
            AdapterError: If the API call fails or payload cannot be parsed.
        """
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "Duffel-Version": DUFFEL_VERSION,
        }
        payload = {
            "data": {
                "slices": [
                    {
                        "origin": origin,
                        "destination": destination,
                        "departure_date": departure_date,
                    }
                ],
                "passengers": [{"type": "adult"} for _ in range(adults)],
                "cabin_class": "economy",
            }
        }

        try:
            response = requests.post(
                OFFER_REQUESTS_URL,
                headers=headers,
                json=payload,
                timeout=DEFAULT_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise AdapterError(f"Duffel flight search request failed: {e}") from e
        except ValueError as e:
            raise AdapterError(f"Duffel response was not valid JSON: {e}") from e

        offers = data.get("data", {}).get("offers")
        if offers is None:
            return []
        if not isinstance(offers, list):
            raise AdapterError("Duffel response missing offers list")

        flights: list[FlightModel] = []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            flights.append(self._map_offer_to_flight_model(offer))

        return flights

    def _map_offer_to_flight_model(self, offer: dict[str, Any]) -> FlightModel:
        """Map a single Duffel offer to FlightModel.

        Args:
            offer: Single offer dict from Duffel response.

        Returns:
            Normalized FlightModel.

        Raises:
            AdapterError: If required fields are missing or malformed.
        """
        slices = offer.get("slices", [])
        first_slice = slices[0] if slices else {}
        segments = first_slice.get("segments", [])
        segment = segments[0] if segments else {}

        operating_carrier = segment.get("operating_carrier", {})
        carrier_code = operating_carrier.get("iata_code")
        flight_number = segment.get("operating_carrier_flight_number")
        departure_at = segment.get("departing_at")
        arrival_at = segment.get("arriving_at")
        duration = first_slice.get("duration")

        origin_iata = segment.get("origin", {}).get("iata_code")
        destination_iata = segment.get("destination", {}).get("iata_code")

        total_amount = self._to_decimal(offer.get("total_amount"))
        base_amount = self._to_decimal(offer.get("base_amount"))
        tax_amount = self._to_decimal(offer.get("tax_amount"))
        currency = offer.get("total_currency")

        passengers = segment.get("passengers", [])
        first_passenger = passengers[0] if passengers else {}
        cabin = first_passenger.get("cabin", {})
        cabin_class = cabin.get("name")
        fare_basis = first_passenger.get("fare_basis_code")
        fare_brand_name = first_slice.get("fare_brand_name")

        baggages = first_passenger.get("baggages", [])
        checked_bags = self._get_baggage_quantity(baggages, "checked")
        carry_on_bags = self._get_baggage_quantity(baggages, "carry_on")

        conditions = offer.get("conditions", {})
        refund_info = conditions.get("refund_before_departure")
        change_info = conditions.get("change_before_departure")
        refund_allowed = refund_info.get("allowed") if isinstance(refund_info, dict) else None
        change_allowed = change_info.get("allowed") if isinstance(change_info, dict) else None

        try:
            return FlightModel(
                source=SOURCE_DUFFEL,
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
                fare_brand=fare_brand_name,
                checked_bags=checked_bags,
                carry_on_bags=carry_on_bags,
                refund_allowed=refund_allowed,
                change_allowed=change_allowed,
            )
        except Exception as e:
            raise AdapterError(f"Failed to normalize Duffel offer: {e}") from e

    def _to_decimal(self, value: Any) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _get_baggage_quantity(self, baggages: list, baggage_type: str) -> int | None:
        for bag in baggages:
            if isinstance(bag, dict) and bag.get("type") == baggage_type:
                quantity = bag.get("quantity")
                if isinstance(quantity, int):
                    return quantity
        return None