# Automation

## Purpose

TradeForge uses GitHub Actions for repeatable validation, packaging, documentation checks, governance enforcement, and container publishing. Pull requests and pushes trigger the required checks automatically.

## Workflow Inventory

| Workflow | Triggers | Result |
| --- | --- | --- |
| CI | Pull request and push to `main` | Runs Ruff, Pytest, package build, and container build. Publishes the container to GHCR after a successful `main` build. |
| Docs | Pull request and push to `main` | Lints durable documentation and verifies every documentation section entry point. |
| Governance | Pull request, push to `main`, manual dispatch, and Monday schedule | Validates the four living root files and rejects change sets that omit one. |

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

A failed check stops the workflow and reports the specific missing file or invalid structure in the job log. No workflow silently edits governance content because the assessment, rationale, and roadmap priority require project context.

Repeated CI issue creation and notification routing remain tracked in `FUTURE-UPGRADES.md`.

## Security Boundary

Workflows use read only repository permissions unless publishing requires GHCR package write access. Local databases, reports, `.env`, and credentials remain excluded from Git.

## Cross Links

* [contributing](../contributing/README.md)
* [roadmap](../roadmap/README.md)
