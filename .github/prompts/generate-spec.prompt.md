# Generate Spec

You are writing `spec.md` for a TradeForge feature package.

Start from the package `requirements.md`.

Project rules:

1. Keep the existing repo layout unless change is justified.
2. Name the exact modules, commands, tests, and docs that will change.
3. Be explicit about data model impact, migration impact, and simulation impact.
4. If the feature changes trading behavior, describe timing and order lifecycle clearly.

Use this shape:

```md
# Specification

## Summary

## Current State

## Proposed Design

## Module Changes

## Data Model And Migration Impact

## CLI Impact

## API Impact

## Reporting Impact

## Testing Strategy

## Risks

## Rollout Notes
```
