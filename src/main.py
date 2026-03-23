"""Flight API Data Quality Platform — Pipeline Orchestrator.

Runs the complete pipeline:
1. Load routes from config/routes.yaml
2. Extract flights from Amadeus and Duffel per route
3. Save raw responses to Bronze layer
4. Validate flights against quality rules
5. Score flights and populate quality metadata
6. Save normalized flights to Silver layer
7. Save scored flights to Gold layer
8. Persist results to PostgreSQL
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from src.adapters.providers.amadeus_adapter import AmadeusAdapter
from src.adapters.providers.duffel_adapter import DuffelAdapter
from src.adapters.repositories.file_repository import FileRepository
from src.adapters.repositories.postgres_repository import PostgresRepository
from src.domain.services.flight_scoring_service import FlightScoringService
from src.domain.services.flight_validation_service import (
    FlightValidationService,
    VALIDATION_RULES,
)

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DATA_PATH = Path("data")
CONFIG_PATH = Path("config/routes.yaml")


def load_config() -> dict:
    """Load routes and parameters from config/routes.yaml."""
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


def main() -> None:
    """Run the Flight API Data Quality pipeline."""

    # --- Load config ---
    config = load_config()
    routes = config["routes"]
    adults = config["adults"]

    logger.info("Starting Flight API Data Quality Pipeline")
    logger.info("Routes loaded: %d", len(routes))

    # --- Initialize adapters ---
    amadeus = AmadeusAdapter(
        amadeus_api_key=os.getenv("AMADEUS_API_KEY", ""),
        amadeus_api_secret=os.getenv("AMADEUS_API_SECRET", ""),
    )
    duffel = DuffelAdapter(
        access_token=os.getenv("DUFFEL_ACCESS_TOKEN", ""),
    )
    file_repo = FileRepository(base_path=DATA_PATH)
    postgres_repo = PostgresRepository(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "flight_dq"),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
    )
    validator = FlightValidationService(rules=VALIDATION_RULES)
    scorer = FlightScoringService()

    all_flights = []

    # --- Process each route ---
    for route in routes:
        origin = route["origin"]
        destination = route["destination"]
        date = route["date"]

        logger.info("Processing route: %s → %s on %s", origin, destination, date)

        # Extract from Amadeus
        try:
            import requests
            token = amadeus._get_token()
            response = requests.get(
                "https://test.api.amadeus.com/v2/shopping/flight-offers",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "originLocationCode": origin,
                    "destinationLocationCode": destination,
                    "departureDate": date,
                    "adults": adults,
                    "max": 5,
                },
                timeout=30,
            )
            response.raise_for_status()
            file_repo.save_bronze(response.json(), "amadeus")
            amadeus_flights = amadeus.search_flights(origin, destination, date, adults)
            logger.info("Amadeus %s→%s: %d flights", origin, destination, len(amadeus_flights))
            all_flights.extend(amadeus_flights)
        except Exception as e:
            logger.error("Amadeus failed for %s→%s: %s", origin, destination, e)

        # Extract from Duffel
        try:
            import requests
            response = requests.post(
                "https://api.duffel.com/air/offer_requests",
                headers={
                    "Authorization": f"Bearer {os.getenv('DUFFEL_ACCESS_TOKEN', '')}",
                    "Content-Type": "application/json",
                    "Duffel-Version": "v2",
                },
                json={
                    "data": {
                        "slices": [{"origin": origin, "destination": destination, "departure_date": date}],
                        "passengers": [{"type": "adult"} for _ in range(adults)],
                        "cabin_class": "economy",
                    }
                },
                timeout=30,
            )
            response.raise_for_status()
            file_repo.save_bronze(response.json(), "duffel")
            duffel_flights = duffel.search_flights(origin, destination, date, adults)
            logger.info("Duffel %s→%s: %d flights", origin, destination, len(duffel_flights))
            all_flights.extend(duffel_flights)
        except Exception as e:
            logger.error("Duffel failed for %s→%s: %s", origin, destination, e)

    if not all_flights:
        logger.error("No flights found — pipeline aborted")
        return

    # --- Validate ---
    logger.info("Validating %d flights...", len(all_flights))
    validated = [validator.validate(flight) for flight in all_flights]

    # --- Score ---
    logger.info("Scoring flights...")
    scored = [scorer.score(flight) for flight in validated]

    # --- Save Silver ---
    silver_path = file_repo.save_silver(scored)
    logger.info("Silver saved: %s", silver_path)

    # --- Save Gold ---
    gold_path = file_repo.save_gold(scored)
    logger.info("Gold saved: %s", gold_path)

    # --- Save to PostgreSQL ---
    postgres_repo.save_results(scored)
    logger.info("Results saved to PostgreSQL")

    # --- Summary ---
    valid = sum(1 for f in scored if f.quality_metadata and f.quality_metadata.is_valid_flight)
    invalid = len(scored) - valid
    avg_score = sum(f.quality_metadata.dq_score for f in scored if f.quality_metadata) / len(scored)

    logger.info("Pipeline complete — %d flights processed", len(scored))
    logger.info("Valid: %d | Invalid: %d | Avg score: %.2f", valid, invalid, avg_score)


if __name__ == "__main__":
    main()