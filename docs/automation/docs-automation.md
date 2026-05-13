# Docs Automation

## Objective

Treat documentation as a maintained product surface with link validation, style checks, and navigation checks.

## Recommended GitHub Actions

* `docs-lint`
  * run Markdown lint
  * run spelling on docs focused dictionaries
  * fail on broken relative links
* `docs-nav-check`
  * ensure every `docs/*/README.md` is linked from `docs/README.md`
  * ensure README links point to real tracked docs
* `docs-freshness-check`
  * compare current environment variables against docs references
  * compare CLI commands against README and docs examples
* `docs-preview`
  * build a future MkDocs site on pull requests
  * publish preview artifacts for review
* `wiki-promotion-reminder`
  * optional scheduled check for stale research items that should move to `docs/`

## Recommended Local Checks

* `python -m markdownlint_cli2 "README.md" "docs/**/*.md"`
* `python -m pytest -q`
* a repo local link validation script

## README Refresh Ideas

* derive feature bullets from tagged docs sections
* derive docs links from `docs/README.md`
* refresh command examples from CLI help snapshots

## GitHub Pages Ideas

* keep `docs/` as the canonical source
* generate MkDocs navigation from the same folder layout
* publish on tagged releases or merges to `main`

## Future Doc Generation Concepts

* generate API docs from OpenAPI into `docs/api/generated/`
* generate settings tables from `config.py`
* generate migration inventory from Alembic revision files
