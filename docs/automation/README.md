# Automation

## Purpose

TradeForge uses one local maintenance command and GitHub Actions for repeatable operations. Both paths stop on failure and publish diagnostic state.

## Local Maintenance

`tradeforge run-maintenance` performs these steps in order:

1. initialize or migrate the configured database
2. validate and upsert each `data/imports/<TICKER>.csv`
3. refresh quotes for every open position with retry and completeness checks
4. create and integrity check an online SQLite backup
5. remove backups beyond `TRADEFORGE_BACKUP_RETENTION_COUNT`
6. write a timestamped report and `data/automation/latest.json`

A failed step returns exit code 1, writes a failure report, and posts JSON to `TRADEFORGE_FAILURE_WEBHOOK_URL` when configured. Quote backoff is capped by `TRADEFORGE_QUOTE_RETRY_MAX_SECONDS` so one delay cannot exceed the scheduled execution budget. Databases, backups, reports, imported files, and credentials remain untracked.

Install the daily Windows task from an activated environment:

```powershell
.\scripts\Install-TradeForgeScheduledTask.ps1 -DailyAt "02:00" -RunNow
```

Task Scheduler starts missed runs when the host returns and retries failures three times at five minute intervals.

## Workflow Inventory

| Workflow | Triggers | Result |
| --- | --- | --- |
| CI | Pull request and push to `main` | Checks Ruff and lock drift, treats test warnings as failures, tests Python 3.11, 3.13, and the container's Python 3.14 runtime, builds the package, starts and health checks the container, then publishes to GHCR after a successful `main` build. |
| Docs | Pull request and push to `main` | Installs locked Markdown tooling, runs the path safe PowerShell lint wrapper, and verifies every documentation section entry point. |
| Governance | Pull request, push to `main`, manual dispatch, and Monday schedule | Validates the four living root files and rejects change sets that omit one. |
| Security | Pull request, manual dispatch, and Monday schedule | Reviews dependency changes and audits the installed Python dependency set for known vulnerabilities. |
| Release | Semantic version tag | Validates the tag against package metadata, reruns release checks, builds artifacts, and creates a GitHub release. |

## Governance Contract

Every repository change must update:

* `CHANGELOG.md`
* `ASSESSMENT.md`
* `FUTURE-UPGRADES.md`
* `COMPLETED-UPGRADES.md`

The validator also checks exact filename casing, newest first dates, changelog summary and reason fields, the assessment section and length contract, the three roadmap tiers, and completed upgrade date order.

Run the same check before handoff:

```powershell
./scripts/Test-ProjectGovernance.ps1 -CheckWorkingTree
```

## Failure Behavior

A failed check stops the workflow and reports the specific error in the job log. Protected `main` requires strict CI, Docs, and Governance results, resolved conversations, linear history, and a pull request. Only squash merging is enabled.

Repeated CI issue creation and notification routing remain tracked in `FUTURE-UPGRADES.md`.

## Security Boundary

Workflows use read only repository permissions unless publishing requires GHCR package or GitHub release write access. External actions are pinned to full commit SHAs and Dependabot keeps those references current. Local databases, reports, `.env`, and credentials remain excluded from Git.

## Release Tags

Push a `vMAJOR.MINOR.PATCH` tag only after the value matches `project.version` in `pyproject.toml`. The release workflow rejects mismatched tags and uploads the built wheel and source distribution to the GitHub release.

## Cross Links

* [contributing](../contributing/README.md)
* [roadmap](../roadmap/README.md)
