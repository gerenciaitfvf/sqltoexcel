# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project snapshot
- Desktop app (PyQt6) that executes `.sql` files against SQL Server and exports query results to `.xlsx`.
- Entry point: `main.py`.
- Main runtime folders expected by the app:
  - `Querys/` for input SQL scripts (scanned at app startup).
  - `output/` for generated Excel files.

## Source-of-truth docs and rule files
- Read `README.md` for project intent and usage flow.
- Existing `AGENTS.MD` contains legacy/overlong guidance; prefer this `AGENTS.md` for day-to-day engineering work.
- No `WARP.md`, `CLAUDE.md`, `.cursor/rules/`, `.cursorrules`, or `.github/copilot-instructions.md` were found.

## Environment and dependency notes
- Python 3.10+.
- Install dependencies:
  - `pip install -r requirements.txt`
- SQL Server connectivity in code is currently implemented with `pymssql` (`src/database/connection.py`), even though docs mention `pyodbc`.
- Runtime config is loaded from `.env` using:
  - `DB_HOST`
  - `DB_PORT` (optional, defaults to `1433`)
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASS`

## Common commands
- Create and activate venv (Linux/macOS):
  - `python -m venv venv`
  - `source venv/bin/activate`
- Install deps:
  - `pip install -r requirements.txt`
- Run app locally:
  - `python main.py`
- Build executable (PyInstaller spec exists):
  - `pyinstaller SQL2Excel.spec`

## Tests and linting status
- There is currently no committed test suite (`tests/` not present) and no lint/format config in repository files.
- If adding tests with pytest, use:
  - Run all tests: `python -m pytest -q`
  - Run one test: `python -m pytest tests/test_executor.py::test_apply_date_filter -q`

## High-level architecture (big picture)
- UI orchestration lives in `src/gui/main_window.py`:
  - Loads available `.sql` files from `Querys/`.
  - Detects whether selected SQL needs date parameter replacement.
  - Executes queries in a worker thread (`ExecuteQueryThread`) to keep UI responsive.
  - Exports returned DataFrame to Excel and reports status/errors to the user.
- Connection/config layer: `src/database/connection.py`:
  - Manages `.env` read/write (`python-dotenv`) and DB connection lifecycle.
  - Handles both source execution and PyInstaller-frozen execution paths.
- Query execution layer: `src/database/executor.py`:
  - Applies date replacement for `comp.Fecha` / `mb.Fecha` filters before execution.
  - Executes SQL into a Pandas DataFrame via `pd.read_sql`.
  - Current implementation writes debug SQL to `/tmp/debug_last_query.sql`.
- Export layer: `src/export/excel_writer.py`:
  - Writes DataFrame rows/headers into an OpenPyXL workbook.
  - Stores outputs in `output/` with timestamped names.

## Important implementation details to keep in mind
- Date regex replacement must use `\g<1>`/`\g<2>` style groups (already implemented) to avoid numeric ambiguity in replacement strings.
- SQL files are currently read with `latin-1` encoding in both UI and executor paths.
- `ConfigDialog` references a `driver` field, but `ConnectionManager.config` does not define it; treat this mismatch carefully if touching DB config UI.
