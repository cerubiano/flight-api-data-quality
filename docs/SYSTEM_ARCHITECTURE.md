# System Architecture — Flight API Data Quality Platform

## 1. Overview

This platform ingests, normalizes, and scores the quality of flight 
data returned by multiple API sources through the flight search endpoint.
It combines Medallion Architecture (Bronze → Silver → Gold) with 
Hexagonal Architecture (Ports & Adapters) to ensure clean separation 
between business logic and infrastructure.

---

## 2. Architecture Diagram
```
┌─────────────────────────────────────────────────────┐
│                    DATA SOURCES                      │
│                                                      │
│   ┌─────────────────┐     ┌─────────────────┐       │
│   │     Amadeus     │     │     Duffel      │       │
│   │     (GDS)       │     │     (NDC)       │       │
│   │ GET /v2/shopping│     │ POST /air/offer │       │
│   │ /flight-offers  │     │ _requests       │       │
│   └────────┬────────┘     └────────┬────────┘       │
└────────────┼──────────────────────-┼────────────────┘
             │                       │
             └──────────┬────────────┘
                        │
        ┌───────────────▼───────────────┐
        │          BRONZE LAYER         │
        │    Raw JSON — untouched       │
        │          AWS S3               │
        │ s3://flight-dq/bronze/        │
        │ amadeus/YYYYMMDD_*.json       │
        │ duffel/YYYYMMDD_*.json        │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │          SILVER LAYER         │
        │  Normalized — standard schema │
        │          AWS S3               │
        │ s3://flight-dq/silver/        │
        │ YYYYMMDD_*.parquet            │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │           GOLD LAYER          │
        │   Validated + QA Score        │
        │          AWS S3               │
        │ s3://flight-dq/gold/          │
        │ YYYYMMDD_*.parquet            │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │          POSTGRESQL           │
        │  Validation results + scores  │
        │     Database: flight_dq       │
        │     Table: dq_results         │
        └───────────────┬───────────────┘
                        │
        ┌───────────────▼───────────────┐
        │        TABLEAU PUBLIC         │
        │     Quality Dashboard         │
        │     Public URL                │
        └───────────────────────────────┘
```

---

## 3. Hexagonal Architecture
```
┌──────────────────────────────────────────────────────┐
│                      DOMAIN                          │
│                                                      │
│   models/                  services/                 │
│   flight_model.py          flight_validation_        │
│                            service.py                │
│                            flight_scoring_           │
│                            service.py                │
│                                                      │
│   ports/                                             │
│   provider_port.py         repository_port.py        │
└──────────────────────────────┬───────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────┐
│                    ADAPTERS                          │
│                                                      │
│   providers/               repositories/             │
│   amadeus_adapter.py       file_repository.py        │
│   duffel_adapter.py        postgres_repository.py    │
└──────────────────────────────────────────────────────┘
```

**Ports define contracts. Adapters implement them.**

- `provider_port.py` — contract that every flight API adapter must implement
- `repository_port.py` — contract that every storage adapter must implement
- Adding a new API source requires only a new adapter — domain is never touched

---

## 4. Components

### 4.1 Data Sources

| Source | Type | Endpoint | Environment |
|---|---|---|---|
| Amadeus | GDS | GET /v2/shopping/flight-offers | test.api.amadeus.com |
| Duffel | NDC Aggregator | POST /air/offer_requests | api.duffel.com |

### 4.2 Bronze Layer
- **Purpose:** Store raw API responses without modification
- **Storage:** AWS S3
- **Format:** JSON
- **Path:** `s3://flight-dq/bronze/{source}/{YYYYMMDD_HHMMSS}_{source}.json`
- **Retention:** Permanent — source of truth for all transformations

### 4.3 Silver Layer
- **Purpose:** Normalize data from all sources to a single standard schema
- **Storage:** AWS S3
- **Format:** Parquet (snappy compression)
- **Path:** `s3://flight-dq/silver/{YYYYMMDD_HHMMSS}_normalized.parquet`
- **Key transformation:** Resolve structural differences between Amadeus and Duffel

### 4.4 Gold Layer
- **Purpose:** Apply quality rules and generate scores per dimension
- **Storage:** AWS S3
- **Format:** Parquet (snappy compression)
- **Path:** `s3://flight-dq/gold/{YYYYMMDD_HHMMSS}_validated.parquet`
- **Key output:** Quality score per field, per dimension, per airline, per source

### 4.5 PostgreSQL
- **Purpose:** Store validation results for querying and dashboard
- **Host:** localhost (development)
- **Database:** flight_dq
- **Table:** dq_results
- **Key queries:** Score by source, score by airline, score by dimension

### 4.6 Tableau Public
- **Purpose:** Visualize quality scores and integration health
- **Access:** Public URL
- **Connection:** PostgreSQL localhost
- **Refresh:** Manual per validation run

---

## 5. Data Flow
```
Step 1 — Extraction
Input:  origin, destination, departure_date, adults
Action: Call Amadeus and Duffel flight search endpoints
Output: Raw JSON per source → Bronze layer

Step 2 — Normalization
Input:  Bronze JSON per source
Action: Map each source fields to standard schema via Pydantic
Output: Single normalized schema → Silver layer (Parquet)

Step 3 — Validation
Input:  Silver Parquet
Action: Apply quality rules per dimension
        Completeness — non-null critical fields
        Validity     — IATA standards + ISO 8601 formats
        Consistency  — cross-field validation
        Conformity   — structural compliance
Output: QA Score per field + errors → Gold layer (Parquet)

Step 4 — Storage
Input:  Gold Parquet
Action: Persist validation results to PostgreSQL
Output: dq_results table updated

Step 5 — Visualization
Input:  PostgreSQL dq_results
Action: Tableau Public reads scores
Output: Quality Dashboard — public URL
```

---

## 6. Repository Structure
```
flight-api-data-quality/
    data/
        bronze/
            amadeus/
            duffel/
        silver/
        gold/
    src/
        domain/
            models/
                flight_model.py
            services/
                flight_validation_service.py
                flight_scoring_service.py
            ports/
                provider_port.py
                repository_port.py
        adapters/
            providers/
                amadeus_adapter.py
                duffel_adapter.py
            repositories/
                file_repository.py
                postgres_repository.py
        main.py
    tests/
        test_flight_validation_service.py
        test_flight_scoring_service.py
        test_amadeus_adapter.py
        test_duffel_adapter.py
    docs/
        PRD.md
        SYSTEM_ARCHITECTURE.md
        specs/
            SPEC-001-bronze-layer.md
            SPEC-002-silver-layer.md
            SPEC-003-gold-layer.md
    .cursor/
        rules/
    .env.example
    requirements.txt
    README.md
```

---

## 7. Technology Stack

| Component | Technology | Version |
|---|---|---|
| Language | Python | 3.12 |
| Data processing | Pandas + PyArrow | Latest |
| Data validation | Pydantic | v2 |
| AWS SDK | Boto3 | Latest |
| Cloud storage | AWS S3 | — |
| Database | PostgreSQL | 16 |
| DB connector | Psycopg2 | Latest |
| Dashboard | Tableau Public | Latest |
| Version control | Git + GitHub | — |

---

## 8. Data Dictionary

### Standard Flight Schema — Silver Layer

| Field | Type | Source Amadeus | Source Duffel |
|---|---|---|---|
| `source` | string | — | — |
| `carrier_code` | string | `carrierCode` | `operating_carrier.iata_code` |
| `flight_number` | string | `number` | `operating_carrier_flight_number` |
| `origin_iata` | string | `departure.iataCode` | `origin.iata_code` |
| `destination_iata` | string | `arrival.iataCode` | `destination.iata_code` |
| `departure_at` | datetime | `departure.at` | `departing_at` |
| `arrival_at` | datetime | `arrival.at` | `arriving_at` |
| `duration` | string | `duration` | `duration` |
| `cabin_class` | string | `cabin` | `cabin_class` |
| `fare_basis` | string | `fareBasis` | `fare_basis_code` |
| `fare_brand` | string | `brandedFare` | `fare_brand_name` |
| `base_amount` | decimal | `price.base` | `base_amount` |
| `tax_amount` | decimal | sum of `price.fees` | `tax_amount` |
| `total_amount` | decimal | `price.grandTotal` | `total_amount` |
| `currency` | string | `price.currency` | `total_currency` |
| `checked_bags` | integer | `includedCheckedBags.quantity` | `baggages[checked].quantity` |
| `carry_on_bags` | integer | `includedCabinBags.quantity` | `baggages[carry_on].quantity` |
| `refund_allowed` | boolean | null | `refund_before_departure.allowed` |
| `change_allowed` | boolean | null | `change_before_departure.allowed` |

---

## 9. Environment Variables
```
# Amadeus
AMADEUS_API_KEY=
AMADEUS_API_SECRET=

# Duffel
DUFFEL_ACCESS_TOKEN=

# AWS
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_REGION=ca-central-1
S3_BUCKET_NAME=flight-dq

# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flight_dq
DB_USER=
DB_PASSWORD=
```