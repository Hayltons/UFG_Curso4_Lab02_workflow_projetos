# Repository Guidelines

## Project Structure & Module Organization

`app/` contains the FastAPI backend: `api/` defines routes, `models/` defines contracts and database entities, `services/` owns business rules, and `repositories/` handles SQLAlchemy persistence. `app/database.py` configures SQLite sessions. `frontend/` contains the Streamlit interface and its HTTPX API client. `tests/` mirrors those layers with `test_*.py` files. `docs/` holds the MVP scope and backlog. There is no separate static asset pipeline; the interface uses Streamlit components.

## Build, Test, and Development Commands

Run commands from the repository root with Python 3.11 or newer. Create and activate a virtual environment, then install development dependencies with `python -m pip install -r requirements-dev.txt`. Use `requirements.txt` for runtime dependencies only.

Start the API with `python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`. In a second terminal, set `API_BASE_URL=http://127.0.0.1:8000` using your shell's syntax and run `python -m streamlit run frontend/streamlit_app.py --server.port 8501`. Run `python -m pytest -q` for tests and `python -m pip check` for dependency conflicts. No build or lint command is configured.

## Coding Style & Naming Conventions

Use four-space indentation, type hints, `snake_case` for Python functions and files, and `PascalCase` for classes. Keep validation in Pydantic contracts, workflow and indicator rules in services, and database operations in repositories. The Streamlit UI should call the API through `frontend/api_client.py`; avoid duplicating business calculations in the interface. Preserve the current naming of HTTP routes and use PATCH for project edits.

## Testing Guidelines

Use Pytest for services, API routes, persistence, and the HTTP client; use Streamlit AppTest for interface flows. Name files `test_<module>.py` and tests `test_<behavior>`. Add focused cases for changed behavior, especially validation, phase transitions, history atomicity, and avoiding repeated writes on reruns. Use isolated test databases instead of the local `projects.db`. No numeric coverage threshold is configured.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commits such as `feat: add project REST endpoints`, `fix: use PATCH for project updates`, and `docs: add clone and setup instructions`. Keep commits focused; this project's current review workflow requests one file per commit. PRs should describe the change, link a related issue when one exists, report verification, and include screenshots for visible UI changes. Identify database migration steps when schemas change.

## Configuration and Review Drafts

`.env.example` documents `API_BASE_URL`, but `.env` is not loaded automatically. SQLite files and local review materials are ignored by Git. Treat `README_Rev1.md` and other Rev1 documents as proposals until their changes are approved and implemented. Do not commit local databases, backups, or secrets.
