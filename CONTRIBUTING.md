# Contributing

TradeForge welcomes focused fixes and research-platform improvements that preserve simulated, local execution.

## Development Setup

```powershell
py -3.13 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
npm ci --ignore-scripts
```

Create `.env` from `.env.example`; never commit the populated file.

## Branch And Tag Names

Use `<type>/<short-kebab-case>` for contributor branches, such as `fix/order-accounting`, `docs/security-model`, or `chore/dependency-updates`. Automation branches may use `agent/<short-kebab-case>` or the service's standard prefix.

Release tags must use `vMAJOR.MINOR.PATCH` and exactly match the version in `pyproject.toml`.

## Required Checks

Run the checks that apply before opening a pull request:

```powershell
ruff check .
ruff format --check .
mypy
python -m pytest --cov=tradeforge --cov-report=term-missing -q
python -m build
pip-audit --local --skip-editable
./scripts/Test-Markdown.ps1
./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree
```

Run `docker build -t tradeforge-ci .` when Docker or runtime dependencies change.

## Dependency Lock Updates

Use the CI-pinned uv version to resolve the universal Python 3.11 lock. CI seeds its temporary output from `requirements.lock`, resolves the current `pyproject.toml`, and compares the result. This checks graph consistency without silently upgrading unrelated packages whenever upstream releases change.

For an intentional dependency update, use `uv pip compile pyproject.toml --extra dev --universal --python-version 3.11 --upgrade-package PACKAGE --custom-compile-command "uv pip compile pyproject.toml --extra dev --universal --python-version 3.11 --output-file requirements.lock" --output-file requirements.lock`, replacing `PACKAGE` with the approved package name. Review the entire diff and refresh the SHA-256 in `requirements.lock.provenance.json` over UTF-8 lock bytes with CRLF normalized to LF. Run the installed dependency audit, environment doctor, and applicable tests. Do not suppress advisories or remove lock verification to make CI pass.

## Change Rules

1. Add or update tests for behavior changes.
2. Use Alembic for persisted schema changes.
3. Update the canonical documentation when commands, APIs, configuration, or behavior change.
4. Keep exploratory notes in the Wiki until they become durable.
5. Update `CHANGELOG.md`, `ASSESSMENT.md`, `FUTURE-UPGRADES.md`, and `COMPLETED-UPGRADES.md` in every change set.
6. Remove credentials, private data, local databases, and generated reports before committing.

The documentation model is described in:

* [docs/contributing/README.md](./docs/contributing/README.md)
* [docs/contributing/documentation-governance.md](./docs/contributing/documentation-governance.md)
* [docs/contributing/wiki-strategy.md](./docs/contributing/wiki-strategy.md)

## Accessibility

Follow [ACCESSIBILITY.md](./ACCESSIBILITY.md) when changing documentation, CLI output, or the dashboard. Include relevant keyboard, zoom, screen-reader, and readability checks in the pull request, and state what was not tested. Do not claim accessibility conformance without supporting evidence.

## Pull Requests

Use an imperative title and explain the reason, operator impact, validation, and remaining risk. The repository is optimized for squash merges so each pull request should represent one coherent change.

Report vulnerabilities privately according to [SECURITY.md](./SECURITY.md). All participation is subject to [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md).
