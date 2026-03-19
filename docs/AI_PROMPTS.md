# AI-Assisted Development Log

## Methodology
This project was built using Cursor Agent in Plan mode.
Each prompt was designed to respect the architecture defined 
in .cursor/rules/ and docs/ before any code was generated.

## Prompt Log

### Phase 1 — Project Structure
**Prompt:**
Read all files in .cursor/rules/ and docs/ and summarize:
1. The architecture pattern used
2. The folder structure you will create
3. The SOLID principles that apply
Do not create anything yet.

Create the complete project folder structure with all 
necessary __init__.py files as defined in project.mdc.
Do not write any implementation code.

### step code:
1. exceptions.py          ← base de errores
2. flight_model.py        ← schema Pydantic
3. provider_port.py       ← contrato de proveedores
4. repository_port.py     ← contrato de repositorios
5. flight_validation_service.py  ← reglas de calidad
6. flight_scoring_service.py     ← scoring
7. amadeus_adapter.py     ← integración Amadeus
8. duffel_adapter.py      ← integración Duffel
9. file_repository.py     ← Bronze/Silver/Gold local
10. postgres_repository.py ← PostgreSQL
11. main.py               ← orquestador

### Phase 2 — Domain Models
**exceptions.py**
Read domain.mdc and python.mdc. 
Implement src/domain/exceptions.py exactly as defined 
in domain.mdc — Exceptions section.

**flight_model.py**
Read domain.mdc and python.mdc.
Implement src/domain/models/flight_model.py with:
- FlightModel using Pydantic v2
- QualityMetadata nested model
- All fields defined in domain.mdc — Required Fields and Optional Fields sections
- Field validators for carrier_code, origin_iata, destination_iata
- No implementation logic — only the model definition

### Lesson Learned — Be explicit about class structure
Prompt: "nested model" caused Cursor to create QualityMetadata 
as an inner class. Correct term: "separate top-level class 
in the same file".

Refactor src/domain/models/flight_model.py:
Move QualityMetadata outside of FlightModel as a separate 
top-level class in the same file. FlightModel should reference 
QualityMetadata as an external type, not define it internally.
Keep all other code exactly as is.

**provider_port.py**
Read domain.mdc and python.mdc.
Implement src/domain/ports/provider_port.py with:
- Abstract base class FlightProviderPort
- Single abstract method search_flights as defined in domain.mdc
- Google style docstring
- No implementation — only the contract

**repository_port.py**
Read domain.mdc and python.mdc.
Implement src/domain/ports/repository_port.py with:
- Abstract base class RepositoryPort
- Four abstract methods as defined in domain.mdc: 
  save_bronze, save_silver, save_gold, save_results
- Google style docstrings on each method
- Import Path from pathlib
- No implementation — only the contract

**flight_validation_service.py**
Read domain.mdc, python.mdc and SPEC-003-gold-layer.md.
Implement src/domain/services/flight_validation_service.py with:
- Abstract base class ValidationRule with rule_id, dimension, severity, penalty
- Abstract method validate() that returns error_code string or None
- Concrete rule classes for ALL rules defined in domain.mdc Rules Registry
- FlightValidationService class that applies all rules to a FlightModel
- VALIDATION_RULES registry as a list of all concrete rule instances
- Use FlightModel from domain models
- Use ValidationError from domain exceptions
- Google style docstrings
- No magic numbers — use named constants for penalties

### Lesson Learned — Specify data flow between files
When a service modifies a model, specify explicitly:
1. What field needs to exist in the model
2. How the service assigns it
Cursor does not automatically analyze cross-file dependencies 
when files are created in separate prompts.

There is a design issue in flight_validation_service.py.
FlightModel does not have a failed_rules field, so using 
object.__setattr__ is a hack that violates Pydantic immutability.

Fix this in three steps:
1. Add failed_rules: list[str] = Field(default_factory=list) 
   to FlightModel in flight_model.py
2. Set frozen=False in FlightModel ConfigDict to allow 
   field assignment after creation
3. Replace object.__setattr__(flight, "failed_rules", failed_rules)
   with flight.failed_rules = failed_rules in flight_validation_service.py

Keep all other code exactly as is.

**flight_scoring_service.py.**
Read domain.mdc, python.mdc and SPEC-003-gold-layer.md.
Implement src/domain/services/flight_scoring_service.py with:
- PENALTY_MAP dictionary mapping each rule_id to its penalty value
  using the severity matrix defined in SPEC-003
- FlightScoringService class with a single score() method
- score() receives a FlightModel with failed_rules populated
- score() calculates dq_score by subtracting cumulative penalties from 1.0
- score() floors dq_score at 0.0
- score() sets is_valid_flight to True if dq_score >= 0.5
- score() populates quality_metadata on the FlightModel
- score() returns the FlightModel with quality_metadata populated
- Import QualityMetadata and FlightModel from domain models
- Import ScoringError from domain exceptions
- Google style docstrings

**amadeus_adapter.py**

Read project.mdc, python.mdc, domain.mdc and SPEC-002-silver-layer.md.
Implement src/adapters/providers/amadeus_adapter.py with:
- AmadeusAdapter class implementing FlightProviderPort
- Constructor receives amadeus_api_key and amadeus_api_secret as strings
- Private method _get_token() that authenticates with Amadeus OAuth2
  POST https://test.api.amadeus.com/v1/security/oauth2/token
- search_flights() method that:
  1. Calls _get_token() to get Bearer token
  2. Calls GET https://test.api.amadeus.com/v2/shopping/flight-offers
     with origin, destination, departure_date, adults, max=5
  3. Maps raw response to list[FlightModel] using field mapping 
     defined in SPEC-002 Data Dictionary
  4. Returns list[FlightModel]
- Use requests library for HTTP calls
- Raise AdapterError on any HTTP error or connection failure
- Save raw response to bronze layer — NO, that is FileRepository's job
- Google style docstrings
- No magic numbers — use named constants for URLs and limits