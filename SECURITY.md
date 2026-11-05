# Security Policy

## Supported Versions

TradeForge is pre-1.0 software. Security fixes target the current `main` branch and the latest published release, once releases begin. Older snapshots are not maintained.

## Report A Vulnerability Privately

Do not open a public issue for a suspected vulnerability or exposed credential.

Use GitHub's [private vulnerability reporting form](https://github.com/mickpletcher/paper-trade-local-lab/security/advisories/new). Include:

* the affected commit, version, or container tag
* reproduction steps and expected impact
* relevant logs with credentials and personal data removed
* any suggested remediation

The maintainer aims to acknowledge reports within three business days and provide an initial assessment within seven business days. These are targets, not service-level guarantees.

## Security Boundaries

* TradeForge simulates orders and does not route live trades.
* API key authentication is available but disabled by default. Keep the API bound to loopback. For approved network access, enable authentication and use an HTTPS reverse proxy; API keys do not encrypt traffic.
* With authentication enabled, `/health`, `/docs`, `/openapi.json`, and `/redoc` remain public. Restrict their network exposure as needed. See [the security guide](./docs/security/README.md) for the current trust model.
* The supplied Docker Compose configuration publishes port `8000` on host loopback. Review any bind or port changes before allowing network access.
* Alpaca credentials belong only in an ignored local `.env` file or an external secret store. Never commit them.
* `TRADEFORGE_ALPACA_DATA_URL` must use HTTPS and cannot contain embedded credentials.
* Local databases, imported market data, reports, and logs may contain sensitive research information. Protect and back them up accordingly.

## Public Security Questions

Use a normal GitHub issue only for hardening questions that do not reveal an exploitable vulnerability, credential, or private data.
