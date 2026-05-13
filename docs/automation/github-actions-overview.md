# GitHub Actions Overview

## Purpose

This file documents the recommended automation layout for code, docs, and release readiness.

## Current State

The repo already has CI for linting, tests, builds, and container validation.

## Recommended Future Workflow Set

* `ci.yml`
  * code quality and build validation
* `docs.yml`
  * markdown lint
  * link validation
  * docs navigation checks
* `pages.yml`
  * future docs site build and publish
* `release-docs.yml`
  * generate release notes and docs diffs

## Validation Ownership

* code workflows own runtime correctness
* docs workflows own clarity, links, and discoverability
* release workflows own final publication quality
