# SPEC-002: Silver Layer — Data Normalization

## Overview
Transform raw JSON from each source into a single standard schema.
Resolve structural differences between Amadeus and Duffel responses.

## Standard Schema

| Field | Type | Description |
|---|---|---|
| `source` | string | API source: amadeus, duffel |
| `carrier_code` | string | 2-char IATA airline code |
| `flight_number` | string | Flight number |
| `departure_at` | datetime | ISO 8601 departure datetime |
| `arrival_at` | datetime | ISO 8601 arrival datetime |
| `duration` | string | ISO 8601 duration |
| `origin_iata` | string | 3-char IATA origin code |
| `destination_iata` | string | 3-char IATA destination code |
| `cabin_class` | string | economy, business, first |
| `fare_basis` | string | Fare basis code |
| `fare_brand` | string | Fare brand name |
| `base_amount` | decimal | Base fare amount |
| `tax_amount` | decimal | Total tax amount |
| `total_amount` | decimal | Total fare amount |
| `currency` | string | ISO 4217 currency code |
| `checked_bags` | integer | Number of included checked bags |
| `carry_on_bags` | integer | Number of included carry-on bags |
| `refund_allowed` | boolean | Refund permitted before departure |
| `change_allowed` | boolean | Change permitted before departure |
| `ingestion_timestamp` | datetime | Bronze ingestion timestamp |
| `normalization_timestamp` | datetime | Silver normalization timestamp |

## Field Mapping

| Standard Field | Amadeus Source | Duffel Source |
|---|---|---|
| `carrier_code` | `carrierCode` | `operating_carrier.iata_code` |
| `flight_number` | `number` | `operating_carrier_flight_number` |
| `departure_at` | `departure.at` | `departing_at` |
| `arrival_at` | `arrival.at` | `arriving_at` |
| `duration` | `duration` | `duration` |
| `origin_iata` | `departure.iataCode` | `origin.iata_code` |
| `destination_iata` | `arrival.iataCode` | `destination.iata_code` |
| `cabin_class` | `cabin` | `cabin_class` |
| `fare_basis` | `fareBasis` | `fare_basis_code` |
| `fare_brand` | `brandedFare` | `fare_brand_name` |
| `base_amount` | `price.base` | `base_amount` |
| `tax_amount` | sum of `price.fees` | `tax_amount` |
| `total_amount` | `price.grandTotal` | `total_amount` |
| `currency` | `price.currency` | `total_currency` |
| `checked_bags` | `includedCheckedBags.quantity` | `baggages[type=checked].quantity` |
| `carry_on_bags` | `includedCabinBags.quantity` | `baggages[type=carry_on].quantity` |
| `refund_allowed` | null | `conditions.refund_before_departure.allowed` |
| `change_allowed` | null | `conditions.change_before_departure.allowed` |

## Acceptance Criteria
- All fields mapped to standard schema
- Dates converted to ISO 8601
- Currency preserved as-is (conversion is not in scope)
- Null fields are explicitly stored as null (not omitted)
- Output saved as parquet to `data/silver/`
- Output synced to `s3://flight-dq/silver/`