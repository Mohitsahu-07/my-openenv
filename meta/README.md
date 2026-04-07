# OpenEnv Hackathon: Data Custodian

## Environment Description
**Data Custodian** is an `OpenEnv` compliant environment where an AI agent acts as a Data Engineer. The agent is placed into a messy legacy SQLite database and must explore the schema, run SQL commands to clean data formats, deduplicate records, and normalize large flat tables into standard relational structures.

Unlike code generation or support ticket classification, data normalization is **100% deterministic**. The environment grades the agent by running SQL assertions on the resulting database schema and data, satisfying the strict deterministic grading requirement of the hackathon.

## Tasks
* **Easy Task**: Standardize formatting and clean string data in the `users` table.
* **Medium Task**: Extract and map JSON data into new native relational columns in the `orders` table.
* **Hard Task**: Normalize a flat, denormalized `purchases` table into standard `customers` and `orders` tables with foreign keys and no data loss.

## Action & Observation Spaces
### Action Space
* `action_type` (str): `"execute_sql"` or `"submit_task"`
* `query` (str): The SQL statement to run (if `execute_sql`)

### Observation Space
* `last_query` (str): The query just executed
* `query_result` (list): Up to 50 rows returned (if SELECT/PRAGMA)
* `query_error` (str): Any SQL syntax/execution text errors
* `schema_info` (str): Output of the `sqlite_master` table structure

## Setup & Testing
1. Install requirements: `pip install -r requirements.txt`
2. Run Baseline inference: `python inference.py` (Ensure `OPENAI_API_KEY` is set variable)
3. Serve as an API via Docker or FastAPI: `uvicorn app:app --port 7860`

The environment complies with the `OpenEnv` spec via `env.py` providing `step()`, `reset()`, and `state()` functions fully typed with Pydantic. Metadata is recorded in `openenv.yaml`.
