"""Tests for DuffelAdapter using mocked HTTP responses."""

# 1. Standard library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# 2. Third-party
import pytest

# 3. Internal
from src.adapters.providers.duffel_adapter import DuffelAdapter
from src.domain.exceptions import AdapterError
from src.domain.models.flight_model import FlightModel

MOCK_DUFFEL_RESPONSE = {
    "data": {
        "offers": [
            {
                "total_amount": "222.85",
                "base_amount": "188.86",
                "tax_amount": "33.99",
                "total_currency": "USD",
                "conditions": {
                    "refund_before_departure": {"allowed": True},
                    "change_before_departure": {"allowed": False},
                },
                "slices": [
                    {
                        "duration": "PT5H52M",
                        "fare_brand_name": "Basic Economy",
                        "segments": [
                            {
                                "operating_carrier_flight_number": "107",
                                "departing_at": "2026-04-15T10:50:00",
                                "arriving_at": "2026-04-15T13:42:00",
                                "operating_carrier": {"iata_code": "AA"},
                                "origin": {"iata_code": "YUL"},
                                "destination": {"iata_code": "LAX"},
                                "passengers": [
                                    {
                                        "fare_basis_code": "Y20LGTN2",
                                        "cabin": {"name": "economy"},
                                        "baggages": [
                                            {"type": "checked", "quantity": 1},
                                            {"type": "carry_on", "quantity": 1},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]
    }
}


@pytest.fixture
def adapter() -> DuffelAdapter:
    """DuffelAdapter with a fake token."""
    return DuffelAdapter(access_token="duffel_test_fake_token")


def _mock_response(json_data: dict, status_code: int = 201) -> MagicMock:
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def test_search_flights_returns_list_of_flight_models(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], FlightModel)


def test_search_flights_maps_carrier_code(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].carrier_code == "AA"
    assert result[0].flight_number == "107"
    assert result[0].source == "duffel"


def test_search_flights_maps_price(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].total_amount == Decimal("222.85")
    assert result[0].base_amount == Decimal("188.86")
    assert result[0].tax_amount == Decimal("33.99")
    assert result[0].currency == "USD"


def test_search_flights_maps_schedule(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].origin_iata == "YUL"
    assert result[0].destination_iata == "LAX"


def test_search_flights_maps_baggage(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].checked_bags == 1
    assert result[0].carry_on_bags == 1


def test_search_flights_maps_conditions(adapter: DuffelAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(MOCK_DUFFEL_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].refund_allowed is True
    assert result[0].change_allowed is False


def test_search_flights_empty_offers_returns_empty_list(adapter: DuffelAdapter) -> None:
    # Arrange
    empty_response = {"data": {"offers": []}}
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response(empty_response)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result == []


def test_search_flights_http_error_raises_adapter_error(adapter: DuffelAdapter) -> None:
    # Arrange
    import requests as req
    with patch("src.adapters.providers.duffel_adapter.requests.post") as mock_post:
        mock_post.side_effect = req.RequestException("connection error")

        # Act & Assert
        with pytest.raises(AdapterError):
            adapter.search_flights("YUL", "LAX", "2026-04-15")