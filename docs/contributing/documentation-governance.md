# Documentation Governance

## Objective

Keep `README.md`, `docs/`, specs, and the GitHub Wiki aligned without duplicating the same content in four places.

## Source Of Truth Rules

* `README.md` is the landing page.
* `docs/` is the canonical technical documentation source.
* `specs/` owns scoped implementation packages and delivery checkpoints.
* the GitHub Wiki owns exploratory and temporary knowledge.

## Update Rules

Update docs when any of the following change:

* CLI commands
* API routes or payloads
* environment variables
* database schema or migration workflow
* provider support
* plugin contracts
* contributor workflow
* CI or release behavior

## Review Rules

* Every behavior change should update at least one durable doc.
* New directories or major modules should get a matching docs section or link.
* Large refactors should include a docs impact check before merge.
* Temporary design notes should be promoted to `docs/` or deleted after a decision is made.

## Duplication Rules

* Put the full explanation in one canonical file.
* Link to that file from other docs.
* Do not copy large blocks between README, docs, and wiki pages.

## AI Friendly Standards

* Keep one topic per file.
* Use stable headings.
* Use explicit nouns in titles.
* Put operational constraints near the top.
* Avoid vague section names such as `notes` or `misc`.

## Ownership Model

* platform docs are owned by the main maintainers
* feature docs are owned by the feature author until handoff
* docs debt should be tracked in code review or in `docs/roadmap/documentation-roadmap.md`
