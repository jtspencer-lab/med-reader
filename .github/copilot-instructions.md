## MedDocReader — Copilot instructions for code changes

This file gives concise, actionable context to help an AI coding assistant be productive in this repo.

1) Purpose & quick contract
- Goal: implement and modify features around document ingestion, Azure Form Recognizer extraction, spaCy NLP, persistence to PostgreSQL, and a small FastAPI/templated web UI.
- Inputs: code edits, unit tests in `tests/`, environment variables in `.env` (see `README.md`).
- Outputs: runnable app via `python app/main.py` or `uvicorn app.main:app`, Docker via `docker-compose up -d`.

2) Big-picture architecture (where to look)
- Entry point: `app/main.py` — sets up logging, calls `init_database()` and returns the FastAPI app in `app/web/routes`.
- Configuration: `app/config.py` (dataclasses: `AppConfig`, `DatabaseConfig`, `AzureConfig`, `NLPConfig`). Use these objects (e.g. `config`, `db_config`, `azure_config`, `nlp_config`) rather than reading os.getenv directly.
- Business logic: `app/services/` — service classes follow a pattern: lightweight init, dependency composition (repos + infra clients), public workflow methods (`process_document`, `process_batch`). See `DocumentProcessingService` and `NLPService` for examples.
- Persistence: `app/database/repositories/*` — repositories encapsulate DB CRUD used by services (DocumentRepository, PatientRepository, ProcessingLogRepository).
- Web/UI: `app/web/routes` and templates in `app/web/templates` (dashboard.html, upload.html). The web app mounts at root; API docs at `/docs`.

3) Important patterns & conventions (code examples)
- Services instantiate infra clients in __init__ and catch/log errors inside methods. Example: `AzureFormRecognizerService.__init__` and `extract_text_from_document` in `app/services/__init__.py`.
- Use repository objects for all DB changes. Do not write raw SQL inline—add or modify repository methods under `app/database/repositories`.
- Configuration is centralized in `app/config.py`. Prefer adding a new config value there and referencing the global `config` or specialized dataclass (e.g. `nlp_config`) rather than new os.getenv calls.
- Logging: `app/main.py` configures logging using `config.log_level` and `config.log_file`; new modules should use `logger = logging.getLogger(__name__)`.

4) Run / debug / test commands (Windows PowerShell notes)
- Create venv & install: `python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt`
- Development run: `python app/main.py` (creates uploads/templates folders). For reloading, use `uvicorn app.main:app --reload`.
- Docker: `docker-compose up -d` (see `docker-compose.yml`).
- Tests: `pytest tests/`.
- Formatting/linting: `black app/; flake8 app/; mypy app/` per README.

5) Integration points / external dependencies
- Azure Form Recognizer: `azure.ai.formrecognizer.DocumentAnalysisClient` — endpoint and key come from `azure_config` (env vars `AZURE_FORM_RECOGNIZER_ENDPOINT`, `AZURE_FORM_RECOGNIZER_KEY`).
- spaCy: model name comes from env `SPACY_MODEL` => `nlp_config.model_name`. Tests and CI must ensure the model is available or mock NLPService.
- Database: PostgreSQL connection string is `db_config.connection_string`. Database initialization called by `app.database.init_database()` in `app/main.py`. Use `scripts/migrate.py` for migrations.

6) Error handling and return shapes
- Services return `ProcessingResult` objects and log failures. When editing service flows, preserve these return objects and the `success`/`errors` fields so callers (web/API) keep consistent behavior.
- On failures, services tend to update document status via repo calls (e.g. `ProcessingStatus.FAILED`) — maintain this pattern when adding failure branches.

7) Small examples to copy/paste
- Call batch processing from tests or scripts:
  ```py
  from app.services import DocumentProcessingService
  service = DocumentProcessingService()
  results = service.process_batch(r"C:\path\to\documents")
  ```
- Add config setting:
  - add field to `AppConfig` in `app/config.py`, then reference `config.<name>` in code.

8) Where to add tests
- Unit-test services in `tests/services/test_*.py`. Mock external clients (Azure, spaCy, DB repos). Integration tests can target `tests/integration/` with a test DB.

9) Files/locations to check before PR
- `app/config.py` — adding config fields
- `app/services/__init__.py` — service workflow patterns
- `app/database/repositories/` — repository API and transaction patterns
- `app/web/routes/` — API and template endpoints
- `scripts/` — migration/init helpers

If anything in this file is unclear or you'd like me to expand a specific part (examples of mocking Azure/spaCy, adding a new repo method, or generating a unit test scaffold), tell me which area and I'll iterate.
