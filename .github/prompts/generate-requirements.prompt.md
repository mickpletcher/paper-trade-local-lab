# Generate Requirements

You are writing `requirements.md` for a TradeForge feature package.

Project rules:

1. TradeForge is a local first paper trading and strategy testing lab.
2. The repo currently centers on offline simulation, CSV import, SQLite persistence, CLI workflows, markdown reports, and a minimal API.
3. Requirements must preserve current working behavior unless the feature explicitly replaces it.
4. Favor precise functional statements over vague goals.

Output rules:

1. Write clear problem framing.
2. State business or user need in local simulation terms.
3. Separate functional requirements from non functional constraints.
4. List out of scope items explicitly.
5. Include acceptance criteria that can be tested locally.

Use this shape:

```md
# Requirements

## Problem

## Goals

## Non Goals

## Functional Requirements

## Non Functional Requirements

## Acceptance Criteria

## Open Questions
```
