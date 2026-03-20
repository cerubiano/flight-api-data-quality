import pytest
from decimal import Decimal
from datetime import datetime, UTC
from src.domain.models.flight_model import FlightModel


@pytest.fixture
def valid_amadeus_flight() -> FlightModel:
    """Valid flight from Amadeus with all fields present."""
    return FlightModel(
        source="amadeus",
        carrier_code="AC",
        flight_number="775",
        origin_iata="YUL",
        destination_iata="LAX",
        departure_at=datetime(2026, 4, 15, 8, 35, tzinfo=UTC),
        arrival_at=datetime(2026, 4, 15, 11, 42, tzinfo=UTC),
        total_amount=Decimal("178.47"),
        base_amount=Decimal("98.00"),
        tax_amount=Decimal("80.47"),
        currency="EUR",
        cabin_class="economy",
        fare_basis="GNA4A2BA",
        fare_brand="BASIC",
        checked_bags=0,
        carry_on_bags=0,
        refund_allowed=None,
        change_allowed=None,
    )


@pytest.fixture
def valid_duffel_flight() -> FlightModel:
    """Valid flight from Duffel with all fields present."""
    return FlightModel(
        source="duffel",
        carrier_code="AA",
        flight_number="107",
        origin_iata="YUL",
        destination_iata="LAX",
        departure_at=datetime(2026, 4, 15, 10, 50, tzinfo=UTC),
        arrival_at=datetime(2026, 4, 15, 13, 42, tzinfo=UTC),
        total_amount=Decimal("222.85"),
        base_amount=Decimal("188.86"),
        tax_amount=Decimal("33.99"),
        currency="USD",
        cabin_class="economy",
        fare_basis="Y20LGTN2",
        fare_brand="Basic Economy",
        checked_bags=1,
        carry_on_bags=1,
        refund_allowed=True,
        change_allowed=False,
    )
