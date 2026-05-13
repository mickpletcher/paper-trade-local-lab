# Changelog

## 2026-05-12

### Initial repo state

* Added the TradeForge local first paper trading project structure.
* Added the Typer CLI for database setup, CSV imports, backtests, positions, orders, and P and L summaries.
* Added the FastAPI scaffold with health, symbols, positions, orders, and strategy run endpoints.
* Added SQLite persistence, SQLAlchemy models, market data import, broker simulation, backtesting, reporting, and tests.
* Added local data folders for imports and reports.

### Container support

* Added `.dockerignore` for cleaner image builds.
* Added `Dockerfile` to run the API in a Python 3.12 container.
* Added `docker-compose.yml` for persistent local container hosting with the `data` folder mounted into the container.
* Updated `README.md` with Docker and Proxmox oriented setup steps.

### Documentation

* Added this `changelog.md` file.
* Updated `README.md` to link to the changelog from the main project documentation.

### Roadmap planning updates

* Updated `future-upgrades.md` with expanded market coverage for crypto, options, futures, commodities, and forex.
* Added additional expansion items for risk controls, execution realism, analytics, experimentation, and platform hardening.
* Added external platform integration planning for TradingView and broker or exchange connectors.
* Added GitHub integration reference targets and supporting libraries to guide future implementation research.
* Added priority labels (`Now`, `Next`, `Later`) across roadmap items.
* Added a top 10 execution sequence for implementation order.
* Added a completed section in `future-upgrades.md` and annotated completed entries with the 2026-05-12 date.

### Simulation and local setup improvements

* Fixed end of backtest execution so orders created from the final bar do not fill on that same final bar.
* Added sell side inventory validation so the local simulator rejects sells that would create inventory out of thin air.
* Added regression tests for final bar execution behavior, sell side validation, migrations, and an end to end CLI flow.
* Added a bundled sample AAPL dataset plus the `tradeforge seed-sample-data` command for repeatable local setup.
* Replaced ad hoc schema creation with versioned SQLite migrations tracked in `schema_migrations`.

### Assessment and roadmap maintenance

* Added `assessment.md` at the repo root as the current source of truth for project status, strengths, risks, and next steps.
* Updated `future-upgrades.md` to remove completed items that are now part of the current repo baseline.
* Expanded the completed section in `future-upgrades.md` so planning and current state stay aligned.
* Rewrote `README.md` into a detailed operator guide covering local setup, configuration, sample data flow, CLI usage, API usage, Docker usage, testing, and current limitations.

### GitHub Spec workflow

* Added `.github/copilot-instructions.md` with repo specific GitHub Spec rules for TradeForge.
* Added reusable `.github/prompts` files for requirements, spec, plan, tasks, audit, and release readiness.
* Added `specs/README.md` plus the initial `specs/001-core-trading-foundation/` package as the baseline spec for the current MVP.
* Updated `README.md` and `future-upgrades.md` to document the new spec workflow and baseline package.

### Continuous integration

* Added `.github/workflows/ci.yml` to run `python -m pytest -q` on pushes to `main` and on pull requests using Python 3.13.
* Updated `README.md` testing documentation to note the GitHub Actions validation path.

### New spec package

* Added `specs/002-live-market-data-valuation/` with `requirements.md`, `spec.md`, `plan.md`, and `tasks.md`.
* Defined the next planned feature boundary as live quote based valuation only, with all trading and execution remaining local.
* Added `specs/002-live-market-data-valuation/implementation-guide.md` with provider options and a detailed adapter, storage, valuation, API, and testing implementation plan.
* Added `specs/002-live-market-data-valuation/feed-options.md` to rank providers as easy, best, and later for TradeForge.
