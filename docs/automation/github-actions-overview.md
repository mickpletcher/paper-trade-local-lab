# GitHub Actions Overview

## Purpose

This file documents the recommended automation layout for code, docs, and release readiness.

## Current State

CI owns linting, supported runtime tests and typing, correctness mutations, migration performance, Windows scheduling, builds, container validation, and gated image publication. Images publish only when build, container, strict typing, mutation, and migration jobs all pass. Separate workflows own documentation, governance, dependency security, compatibility, prerelease Python, repository policy drift, repeated failure issues, trusted Dependabot doc sync, and attested releases.

Every external action reference is pinned to a full commit SHA. GitHub owned actions plus explicitly selected Astral and Docker families are allowed.

## Validation Ownership

* code workflows own runtime correctness
* docs workflows own clarity, links, and discoverability
* release workflows own final publication quality
