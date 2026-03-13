# Engineering Process & Methodology

## 1. Introduction: The Quality-First Approach
This project follows a **Shift-Left Testing** methodology. This means that quality assurance and testing analysis are performed at the very beginning of the lifecycle, before any code is written. The goal is to prevent bugs through rigorous design rather than just finding them later.

## 2. Requirement Analysis (BDD)
We use **Behavior-Driven Development (BDD)** to define our specifications. Each layer of the pipeline (Bronze, Silver, Gold) is governed by a **Spec** document written in a 'Given/When/Then' format. This eliminates ambiguity and provides clear acceptance criteria for both developers and stakeholders.

## 3. Data Architecture (Medallion Model)
To ensure data integrity and traceability, we implemented the **Medallion Architecture**:
* **Bronze (Raw):** Immutable storage of original API responses.
* **Silver (Standardized):** Data cleaning, type enforcement, and schema validation using Pydantic.
* **Gold (Curated):** Business logic application and Quality Scoring for analytical decision-making.

## 4. System Design (Hexagonal Architecture)
We adopted **Hexagonal Architecture (Ports and Adapters)** to decouple our core business logic (The QA Engine) from external infrastructure (Travel APIs and Databases). This ensures that the system is maintainable, testable, and resilient to external changes.

## 5. Testing Strategy (Quality Assurance Standards)
Our testing strategy is based on **ISTQB international standards**. We apply **Black-Box testing techniques** to ensure the reliability of the data pipeline:
* **Boundary Value Analysis (BVA):** To test limits in prices and dates.
* **Equivalence Partitioning:** To efficiently categorize valid and invalid data sets.
* **Negative Testing:** To verify the system's resilience when handling malformed JSONs or API timeouts.