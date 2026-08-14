# Security

## Purpose

This section defines privacy, trust boundaries, secret handling, and future hardening requirements.

## Intended Contents

* local trust model
* secret handling
* data privacy
* threat assumptions
* plugin and AI safety constraints

## Current Controls

`.env`, SQLite databases, import files, reports, and backups are excluded from Git and the container build context. Supported API launch paths bind to loopback because authentication is not implemented.

The image uses a digest pinned Python base and an unprivileged UID. Compose adds a read only root filesystem, no added Linux capabilities, `no-new-privileges`, and automatic restart. GitHub Actions are SHA pinned and default to read only repository permissions except GHCR publishing.

## Suggested Future Topics

* local-trust-boundary.md
* secrets-management.md
* threat-model.md
* privacy-guarantees.md
* dependency-review.md

## Naming Conventions

* trust docs use `boundary`
* risk docs use `threat` or `risk`
* secret docs use `secret` or `credential`

## File Examples

* `threat-model.md`
* `secrets-management.md`
* `privacy-guarantees.md`

## Cross Links

* [configuration](../configuration/README.md)
* [plugins](../plugins/README.md)
* [ai-integration](../ai-integration/README.md)
