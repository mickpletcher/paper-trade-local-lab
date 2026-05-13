# TradeForge Documentation

This directory is the canonical technical documentation source for TradeForge.

Use it for durable product, engineering, and operator documentation.

Do not use it for temporary notes, open ended brainstorming, or research scratchpads. Those belong in the GitHub Wiki.

## Documentation Goals

* Keep repo level knowledge searchable and stable.
* Support GitHub rendering and direct file links.
* Support future GitHub Pages, MkDocs, or Docusaurus migration.
* Support AI assisted retrieval with predictable file names and scoped topics.
* Support long term contributor onboarding and product hardening.

## Navigation

| Section | Purpose | Start Here |
| --- | --- | --- |
| [architecture](./architecture/README.md) | system shape, boundaries, runtime model | [architecture/README.md](./architecture/README.md) |
| [installation](./installation/README.md) | local setup, environments, deployment entry points | [installation/README.md](./installation/README.md) |
| [configuration](./configuration/README.md) | settings, env vars, profiles, secrets boundaries | [configuration/README.md](./configuration/README.md) |
| [strategies](./strategies/README.md) | strategy authoring and lifecycle | [strategies/README.md](./strategies/README.md) |
| [backtesting](./backtesting/README.md) | simulation, replay, reports, result interpretation | [backtesting/README.md](./backtesting/README.md) |
| [ai-integration](./ai-integration/README.md) | AI coding, research, prompts, safety boundaries | [ai-integration/README.md](./ai-integration/README.md) |
| [market-data](./market-data/README.md) | provider model, imports, replay feeds, normalization | [market-data/README.md](./market-data/README.md) |
| [database](./database/README.md) | schema, migrations, storage, retention | [database/README.md](./database/README.md) |
| [plugins](./plugins/README.md) | extension contracts and plugin lifecycle | [plugins/README.md](./plugins/README.md) |
| [security](./security/README.md) | secrets, privacy, threat model, local trust boundaries | [security/README.md](./security/README.md) |
| [automation](./automation/README.md) | CI, docs automation, release support, maintenance jobs | [automation/README.md](./automation/README.md) |
| [api](./api/README.md) | HTTP contracts, versioning, examples, compatibility | [api/README.md](./api/README.md) |
| [roadmap](./roadmap/README.md) | product direction and documentation roadmap | [roadmap/README.md](./roadmap/README.md) |
| [contributing](./contributing/README.md) | contribution flow, docs governance, wiki strategy | [contributing/README.md](./contributing/README.md) |
| [faq](./faq/README.md) | operator and contributor questions | [faq/README.md](./faq/README.md) |

## Recommended Reading Paths

### New operator

1. [../README.md](../README.md)
2. [installation/README.md](./installation/README.md)
3. [configuration/README.md](./configuration/README.md)
4. [backtesting/README.md](./backtesting/README.md)

### New contributor

1. [../README.md](../README.md)
2. [architecture/README.md](./architecture/README.md)
3. [database/README.md](./database/README.md)
4. [contributing/README.md](./contributing/README.md)
5. [automation/README.md](./automation/README.md)

### AI assistant

1. [architecture/README.md](./architecture/README.md)
2. [configuration/README.md](./configuration/README.md)
3. [database/README.md](./database/README.md)
4. [api/README.md](./api/README.md)
5. [contributing/documentation-governance.md](./contributing/documentation-governance.md)

## Authoring Rules

* One topic per file.
* Use lower case kebab case file names.
* Prefer `README.md` as the section index inside each folder.
* Keep design decisions durable in `docs/`.
* Move exploratory content to the Wiki before it gets stale.
* Link laterally when one doc depends on another doc.

## Shared Templates

* [doc-template.md](./_templates/doc-template.md)
* [how-to-template.md](./_templates/how-to-template.md)
* [research-note-template.md](./_templates/research-note-template.md)
