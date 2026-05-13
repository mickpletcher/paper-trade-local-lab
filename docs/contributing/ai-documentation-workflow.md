# AI Documentation Workflow

## Goal

Use AI assistants to accelerate documentation without allowing them to create drift or vague filler.

## Recommended Workflow

1. Start from live code and tests.
2. Update the canonical doc first.
3. Ask the AI assistant to summarize deltas, not invent architecture.
4. Validate file links, command names, and settings against the repo.
5. Update the README only after the destination docs exist.

## Good AI Tasks

* summarize code paths into a first draft
* generate section outlines from current modules
* compare docs against file inventory
* propose missing examples
* normalize terminology

## Bad AI Tasks

* invent future behavior as if it already exists
* duplicate the same content across multiple files
* rewrite canonical procedures without checking commands
* create generic platform claims with no repo evidence

## Required Validation

* commands must run or match current CLI help
* settings must match `config.py` and `.env.example`
* workflows must match `.github/workflows`
* API docs must match current routes

## Promotion Rule

If an AI generated note is still speculative, move it to the Wiki instead of `docs/`.
