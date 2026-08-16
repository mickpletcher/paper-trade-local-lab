# Plugins

## Purpose

TradeForge exposes an allowlisted in process plugin registry without weakening core defaults.

## Current Contract

Built in strategy, broker, indicator, and report plugins are registered automatically. Installed Python entry points are ignored unless their normalized name is listed in `TRADEFORGE_PLUGIN_ALLOWLIST_JSON`.

```text
TRADEFORGE_PLUGIN_ALLOWLIST_JSON=["approved-plugin"]
```

Names use lower case letters, digits, and single hyphens. Duplicate kind and name pairs fail. Run `tradeforge list-plugins` after every configuration change.

An allowed plugin executes inside the TradeForge process with the operator's filesystem and network permissions. Install and allow only reviewed packages. There is no plugin sandbox, signature verification, API stability promise, or automatic migration access.

Entry point groups are `tradeforge.strategies`, `tradeforge.brokers`, `tradeforge.indicators`, and `tradeforge.reports`. Strategy factories used by the CLI must return `BaseStrategy`.

## Intended Contents

* plugin goals
* extension contracts
* lifecycle hooks
* compatibility model
* packaging guidance

## Suggested Future Topics

* plugin-architecture.md
* provider-plugin-contract.md
* strategy-plugin-contract.md
* plugin-versioning.md
* plugin-security.md

## Naming Conventions

* contracts use the `contract` term
* extension areas use `plugin`
* version docs use compatibility focused names

## File Examples

* `plugin-architecture.md`
* `provider-plugin-contract.md`
* `plugin-versioning.md`

## Cross Links

* [architecture](../architecture/README.md)
* [security](../security/README.md)
