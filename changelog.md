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
