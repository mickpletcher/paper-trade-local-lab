# Security

## Trust Model

TradeForge is a local research application. It does not place live trades, but its database, reports, strategies, logs, and provider credentials can still be sensitive.

The default CLI API binding is loopback-only. The container binds to all interfaces inside the container and publishes port `8000` on the host. Because the API has no authentication, expose it only on a trusted network or behind an authenticated reverse proxy.

## Credentials

Copy `.env.example` to an ignored local `.env` file and store Alpaca credentials there only for development. Production-like deployments should inject secrets from the host or a secret manager. Never place credentials in Docker images, command output, issues, reports, or committed configuration.

Alpaca and failure webhook endpoints are constrained to HTTPS with a hostname and reject embedded URL credentials. Webhook delivery contains only failure status and timestamps; detailed reports, paths, imports, symbols, and errors remain local. Provider errors do not include credential values.

## Current Controls

`.env`, SQLite databases, import files, reports, and backups are excluded from Git and the container build context. The image uses a digest pinned Python base, an unprivileged UID, and a database aware health check. Supported local launch paths must remain behind loopback or another trusted network boundary because authentication is not implemented.

GitHub Actions are SHA pinned and default to read only repository permissions except workflows that publish GHCR images or GitHub releases.

## Repository Controls

The repository uses:

* CodeQL default setup for Python and GitHub Actions
* dependency graph updates and pull-request dependency review
* scheduled Python dependency audits
* Dependabot version updates for Python, npm, Actions, and Docker
* least-privilege workflow permissions and commit-pinned actions
* private vulnerability reporting

Branch protection, secret-scanning status, push protection, and default Actions permissions must also be verified in GitHub settings because those controls are not stored in the repository.

## Data Protection

`.gitignore` and `.dockerignore` exclude local credentials, databases, reports, caches, and build output. Operators remain responsible for file permissions, encrypted backups, log retention, and network controls.

## Reporting

Follow the root [security policy](../../SECURITY.md) for private vulnerability reports.

## Cross Links

* [configuration](../configuration/README.md)
* [plugins](../plugins/README.md)
* [AI integration](../ai-integration/README.md)
