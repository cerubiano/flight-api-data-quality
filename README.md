# Flight API Data Quality Platform

A data pipeline that ingests, normalizes, and scores the quality of 
flight data returned by multiple API sources before it reaches the 
end customer.

---

## Problem

The Content Integration Team at a travel OTA is responsible for the 
health and reliability of multiple flight API integrations. Inconsistent 
or poor-quality data directly impacts customer trust and revenue.

Three core challenges:
- **Validation:** Ensuring new API integrations meet data integrity standards before going live.
- **Monitoring:** Continuous tracking of production API health to detect quality degradation.
- **Visibility:** Data-driven insights for stakeholders to make informed decisions about provider prioritization.

---

## Architecture
```
Amadeus GET /v2/shopping/flight-offers
Duffel  POST /air/offer_requests
        ↓
    Bronze → Silver → Gold
        ↓
    PostgreSQL
        ↓
    Tableau Public
```

Hexagonal Architecture (Ports & Adapters) combined with Medallion 
Architecture (Bronze → Silver → Gold) to ensure clean separation 
between business logic and infrastructure.

---

## Key Data Quality Metrics

- **Completeness:** Percentage of non-null critical fields (Fare Basis, Baggage).
- **Validity:** Adherence to IATA standards and ISO 8601 formats.
- **Consistency:** Cross-field validation (e.g., Total Amount >= Base Amount).
- **Conformity:** Structural compliance of API responses against defined schemas.

---

## Methodology

This project follows a **Shift-Left Testing** approach — quality 
assurance is defined before any code is written.

- **BDD:** Each pipeline layer is governed by a Spec written in 
Given/When/Then format.
- **Hexagonal Architecture:** Core business logic is fully decoupled 
from external APIs and databases.
- **ISTQB Standards:** Testing strategy applies Boundary Value Analysis, 
Equivalence Partitioning, and Negative Testing.

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.12 |
| Data processing | Pandas + PyArrow |
| Data validation | Pydantic v2 |
| Cloud storage | AWS S3 |
| Database | PostgreSQL 16 |
| Dashboard | Tableau Public |
| Version control | Git + GitHub |

---

## Project Structure
```
flight-api-data-quality/
    data/
        bronze/     ← Raw JSON from APIs
        silver/     ← Normalized Parquet
        gold/       ← QA Score Parquet
    src/
        domain/
            models/
            services/
            ports/
        adapters/
            providers/
            repositories/
        main.py
    tests/
    docs/
        PRD.md
        SYSTEM_ARCHITECTURE.md
        specs/
```

---

## Documentation

| Document | Description |
|---|---|
| [PRD](docs/PRD.md) | Problem statement, scope, and success criteria |
| [System Architecture](docs/SYSTEM_ARCHITECTURE.md) | Technical design, data flow, and data dictionary |
| [SPEC-001](docs/specs/SPEC-001-bronze-layer.md) | Bronze layer ingestion specification |
| [SPEC-002](docs/specs/SPEC-002-silver-layer.md) | Silver layer normalization specification |
| [SPEC-003](docs/specs/SPEC-003-gold-layer.md) | Gold layer validation specification |

---

## How to Run

### Prerequisites
- Python 3.12
- PostgreSQL 16
- AWS account with S3 bucket
- Amadeus API credentials
- Duffel API credentials

### Setup
```bash
git clone https://github.com/tuusuario/flight-api-data-quality
cd flight-api-data-quality
pip install -r requirements.txt
cp .env.example .env
# Add your credentials to .env
```

### Run
```bash
python src/main.py
```

---

## Results

*Dashboard and quality scores — coming soon*

---

## Author

Carlos Eduardo Rubiano Robles  
[LinkedIn](#) · [GitHub](#)