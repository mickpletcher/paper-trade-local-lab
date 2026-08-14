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
* The API has no authentication. Keep it bound to loopback or place it behind an authenticated reverse proxy on a trusted network.
* Docker publishes port `8000`; review host firewall and network exposure before using the container outside a development machine.
* Alpaca credentials belong only in an ignored local `.env` file or an external secret store. Never commit them.
* `TRADEFORGE_ALPACA_DATA_URL` must use HTTPS and cannot contain embedded credentials.
* Local databases, imported market data, reports, and logs may contain sensitive research information. Protect and back them up accordingly.

## Public Security Questions

Use a normal GitHub issue only for hardening questions that do not reveal an exploitable vulnerability, credential, or private data.
