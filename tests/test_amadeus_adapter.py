"""Tests for AmadeusAdapter using mocked HTTP responses."""

# 1. Standard library
from decimal import Decimal
from unittest.mock import MagicMock, patch

# 2. Third-party
import pytest

# 3. Internal
from src.adapters.providers.amadeus_adapter import AmadeusAdapter
from src.domain.exceptions import AdapterError
from src.domain.models.flight_model import FlightModel

MOCK_TOKEN_RESPONSE = {
    "access_token": "test_token_123",
    "token_type": "Bearer",
    "expires_in": 1799,
}

MOCK_AMADEUS_RESPONSE = {
    "data": [
        {
            "type": "flight-offer",
            "id": "1",
            "source": "GDS",
            "itineraries": [
                {
                    "duration": "PT6H7M",
                    "segments": [
                        {
                            "departure": {
                                "iataCode": "YUL",
                                "at": "2026-04-15T08:35:00",
                            },
                            "arrival": {
                                "iataCode": "LAX",
                                "at": "2026-04-15T11:42:00",
                            },
                            "carrierCode": "AC",
                            "number": "775",
                            "duration": "PT6H7M",
                        }
                    ],
                }
            ],
            "price": {
                "currency": "EUR",
                "total": "178.47",
                "base": "98.00",
                "grandTotal": "178.47",
                "fees": [
                    {"amount": "40.00", "type": "SUPPLIER"},
                    {"amount": "40.47", "type": "TICKETING"},
                ],
            },
            "travelerPricings": [
                {
                    "fareDetailsBySegment": [
                        {
                            "cabin": "ECONOMY",
                            "fareBasis": "GNA4A2BA",
                            "brandedFare": "BASIC",
                            "includedCheckedBags": {"quantity": 0},
                            "includedCabinBags": {"quantity": 0},
                        }
                    ]
                }
            ],
        }
    ]
}


@pytest.fixture
def adapter() -> AmadeusAdapter:
    """AmadeusAdapter with fake credentials."""
    return AmadeusAdapter(
        amadeus_api_key="fake_key",
        amadeus_api_secret="fake_secret",
    )


def _mock_response(json_data: dict, status_code: int = 200) -> MagicMock:
    """Create a mock requests.Response."""
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data
    mock.raise_for_status.return_value = None
    return mock


def test_search_flights_returns_list_of_flight_models(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(MOCK_AMADEUS_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], FlightModel)


def test_search_flights_maps_carrier_code(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(MOCK_AMADEUS_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].carrier_code == "AC"
    assert result[0].flight_number == "775"
    assert result[0].source == "amadeus"


def test_search_flights_maps_price(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(MOCK_AMADEUS_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].total_amount == Decimal("178.47")
    assert result[0].base_amount == Decimal("98.00")
    assert result[0].currency == "EUR"


def test_search_flights_maps_schedule(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(MOCK_AMADEUS_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].origin_iata == "YUL"
    assert result[0].destination_iata == "LAX"


def test_search_flights_maps_baggage(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(MOCK_AMADEUS_RESPONSE)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result[0].checked_bags == 0
    assert result[0].carry_on_bags == 0


def test_search_flights_empty_data_returns_empty_list(adapter: AmadeusAdapter) -> None:
    # Arrange
    empty_response = {"data": []}
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post, \
         patch("src.adapters.providers.amadeus_adapter.requests.get") as mock_get:
        mock_post.return_value = _mock_response(MOCK_TOKEN_RESPONSE)
        mock_get.return_value = _mock_response(empty_response)

        # Act
        result = adapter.search_flights("YUL", "LAX", "2026-04-15")

    # Assert
    assert result == []


def test_search_flights_http_error_raises_adapter_error(adapter: AmadeusAdapter) -> None:
    # Arrange
    import requests as req
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post:
        mock_post.side_effect = req.RequestException("connection error")

        # Act & Assert
        with pytest.raises(AdapterError):
            adapter.search_flights("YUL", "LAX", "2026-04-15")


def test_get_token_missing_access_token_raises_adapter_error(adapter: AmadeusAdapter) -> None:
    # Arrange
    with patch("src.adapters.providers.amadeus_adapter.requests.post") as mock_post:
        mock_post.return_value = _mock_response({"token_type": "Bearer"})

        # Act & Assert
        with pytest.raises(AdapterError):
            adapter.search_flights("YUL", "LAX", "2026-04-15")