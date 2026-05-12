# Generate Plan

You are writing `plan.md` for a TradeForge feature package.

Start from `requirements.md` and `spec.md`.

Plan rules:

1. Break work into implementation phases that can be validated.
2. Keep schema work before dependent application work.
3. Keep tests and docs in the plan, not as an afterthought.
4. Call out rollback or safe checkpoint boundaries where useful.

Use this shape:

```md
# Plan

## Implementation Phases

## Phase 1

## Phase 2

## Phase 3

## Verification Plan

## Documentation Updates

## Rollback Notes
```
