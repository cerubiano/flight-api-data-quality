-- Flight API Data Quality Platform
-- Database Schema

CREATE TABLE dq_results (
    id                   SERIAL PRIMARY KEY,
    source               VARCHAR(20) NOT NULL,
    carrier_code         VARCHAR(2),
    flight_number        VARCHAR(10),
    origin_iata          VARCHAR(3),
    destination_iata     VARCHAR(3),
    departure_at         TIMESTAMP,
    total_amount         DECIMAL(10,2),
    currency             VARCHAR(3),
    checked_bags         INTEGER,
    carry_on_bags        INTEGER,
    fare_brand           VARCHAR(50),
    refund_allowed       BOOLEAN,
    change_allowed       BOOLEAN,
    score_overall        DECIMAL(3,2),
    failed_rules         JSONB,
    is_valid_flight      BOOLEAN,
    validation_timestamp TIMESTAMP DEFAULT NOW()
);