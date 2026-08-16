# Automation

## Purpose

TradeForge uses one local maintenance command and GitHub Actions for repeatable operations. Both paths stop on failure and publish diagnostic state.

## Local Maintenance

`tradeforge run-maintenance` performs these steps in order:

1. acquire the atomic maintenance lock
2. initialize or migrate the configured database
3. validate, upsert, and archive each `data/imports/<TICKER>.csv`, or quarantine failures with the original retry filename
4. refresh quotes for every open position with jitter, circuit breaking, and completeness checks
5. collect SQLite connection, lock, and WAL checkpoint telemetry
6. create and integrity check an online SQLite backup
7. restore the backup into memory and report recovery time
8. apply backup and report retention while recording nonfatal report deletion failures
9. write a timestamped report and `data/automation/latest.json`

A failed step returns exit code 1, writes the full failure report locally, and can notify a minimal HTTPS webhook, Teams, and SMTP. Teams and email use bounded retry and duplicate suppression. Quote backoff is capped by `TRADEFORGE_QUOTE_RETRY_MAX_SECONDS`. Databases, backups, reports, imported files, and credentials remain untracked.

One SQLAlchemy engine is reused across every database step in a maintenance run and disposed when the run exits. File backed SQLite databases use WAL and the configured bounded busy timeout.

Install the daily Windows task from an activated environment:

```powershell
.\scripts\Install-TradeForgeScheduledTask.ps1 -DailyAt "02:00" -RunNow
```

Task Scheduler starts missed runs when the host returns and retries failures three times at five minute intervals.

The Windows CI job validates the installer contract with mocked cmdlets, then registers, starts, verifies, and removes a disposable real scheduled task.

## Workflow Inventory

| Workflow | Triggers | Result |
| --- | --- | --- |
| CI | Pull request and push to `main` | Validates Windows scheduling, Ruff, formatting, strict Mypy on Python 3.11 through 3.14, lock and environment provenance, warning free tests with an 88 percent coverage floor, correctness mutations, a 25,000 row migration gate, package and container builds, then publishes GHCR provenance and SBOMs only after every gate passes. |
| Docs | Pull request and push to `main` | Installs locked Markdown tooling, runs the path safe PowerShell lint wrapper, and verifies every documentation section entry point. |
| Governance | Pull request, push to `main`, manual dispatch, and Monday schedule | Validates the four living root files and rejects change sets that omit one. |
| Security | Pull request, manual dispatch, and Monday schedule | Reviews dependency severity, licenses, and denied packages and audits installed Python dependencies. |
| Compatibility Canary | Relevant pull request or manual dispatch | Runs the suite and container build before workflow, dependency, or runtime changes merge. |
| Python Prerelease Canary | Tuesday schedule or manual dispatch | Runs nonblocking tests and Mypy on the next Python development release. |
| Repository Policy | Monday schedule or manual dispatch | Detects required check, SHA pin, Actions allowlist, and security feature drift. |
| Repeated Failure Triage | Completed CI or Governance run | Opens or updates one issue after two consecutive failures. |
| Dependabot Living Doc Sync | Trusted Dependabot pull request | Runs base branch automation and commits the four living files before governance validation. |
| Release | Semantic version tag or reusable workflow call | Validates, tests, builds, generates a CycloneDX SBOM, attests artifacts, and creates a GitHub release. |
| Semantic Release | Push to `main` or manual dispatch | Reads conventional commits, runs the full suite plus migration and backtest performance gates, tags an already prepared version and calls Release directly, or creates and automatically squash merges a release preparation pull request. |

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

A failed check stops the workflow and reports the specific error in the job log. Protected `main` requires strict CI, Docs, Governance, dependency review, dependency audit, and CodeQL results, resolved conversations, linear history, and a pull request. Only squash merging is enabled.

Two consecutive CI or governance failures create or update one exact title GitHub issue.

## Security Boundary

Workflows use read only repository permissions unless publishing requires GHCR package or GitHub release write access. Repository policy requires full commit SHA references and restricts Actions to GitHub owned actions plus the committed Astral and Docker action families. Dependabot keeps those references current. Local databases, reports, `.env`, and credentials remain excluded from Git.

## Release Tags

Semantic release automation prepares `feat` changes as minor versions, `fix` and `perf` changes as patch versions, and `!` or `BREAKING CHANGE:` changes as major versions. It updates the package version and all four living files in a reviewable pull request. After creating a validated tag, it directly calls the reusable Release workflow because workflow token tag pushes do not trigger another push workflow. Release rejects mismatched tags and uploads the built wheel, source distribution, CycloneDX SBOM, and GitHub OIDC attestations.

`tradeforge run-dr-drill` measures the newest backup age and restore duration against configured RPO and RTO values. It atomically writes `data/automation/dr-latest.json` and exits nonzero when either objective is missed.

## Cross Links

* [contributing](../contributing/README.md)
* [roadmap](../roadmap/README.md)
