# Security

## Trust Model

TradeForge is a local research application. It does not place live trades, but its database, reports, strategies, logs, and provider credentials can still be sensitive.

The default CLI API binding is loopback-only. The container binds to all interfaces inside the container and publishes port `8000` on the host loopback address. API key authentication is available but disabled by default. Enable it before approved network use and add an HTTPS reverse proxy because API keys do not encrypt traffic.

## Credentials

Copy `.env.example` to an ignored local `.env` file and store Alpaca credentials there only for development. Production-like deployments should inject secrets from the host or a secret manager. Never place credentials in Docker images, command output, issues, reports, or committed configuration.

Alpaca, failure webhook, and Teams endpoints are constrained to HTTPS with a hostname and reject embedded URL credentials. Outbound HTTP paths refuse redirects. Webhook and Teams delivery contains only bounded status context; detailed reports, paths, imports, symbols, and errors remain local. SMTP uses STARTTLS and optional authentication. Provider errors do not include credential values.

## Current Controls

`.env`, SQLite databases, import files, reports, and backups are excluded from Git and the container build context. The image uses a digest pinned Python base, an unprivileged UID, and a database aware health check. Supported local launch paths must remain behind loopback or another trusted network boundary because authentication is not implemented.

API keys are least privilege service identities with tenant, role, expiration, revocation, and last use metadata. Only SHA-256 secret hashes are stored. Raw secrets print once on creation or rotation. Rotation revokes the old identity immediately.

Installed entry point plugins load only through an explicit name allowlist. They execute in process without a sandbox and must be treated as trusted code.

GitHub Actions default to read only repository permissions except workflows that publish GHCR images, GitHub releases, or the semantic release preparation pull request. Repository policy requires full commit SHA references and allows only GitHub owned actions plus the committed Astral and Docker action families.

## Repository Controls

The repository uses:

* CodeQL default setup for Python and GitHub Actions
* dependency graph updates and pull-request dependency review
* scheduled Python dependency audits
* explicit dependency license allow rules and denied package identifiers
* Dependabot version updates for Python, npm, Actions, and Docker
* least-privilege workflow permissions and commit-pinned actions
* private vulnerability reporting
* required dependency review, installed dependency audit, CodeQL, and supported runtime checks before merge
* scheduled required check, action pin, allowlist, and security feature drift verification
* signed lock, release package, and container provenance plus CycloneDX and GHCR SBOM publication

Protected `main` enforces strict required checks, resolved review conversations, linear history, squash merges, and administrator compliance. Dependabot security updates, secret scanning, push protection, default read only Actions permissions, the selected Actions allowlist, and SHA pinning enforcement are verified in GitHub settings.

## Data Protection

`.gitignore` and `.dockerignore` exclude local credentials, databases, reports, caches, and build output. Operators remain responsible for file permissions, encrypted backups, log retention, and network controls.

## Reporting

Follow the root [security policy](../../SECURITY.md) for private vulnerability reports.

## Cross Links

* [configuration](../configuration/README.md)
* [plugins](../plugins/README.md)
* [AI integration](../ai-integration/README.md)
