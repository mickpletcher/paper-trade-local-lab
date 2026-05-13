# GitHub Wiki Strategy

## Role Of The Wiki

The Wiki is for active exploration, early design work, and material that is useful but not yet durable enough for `docs/`.

The Wiki should not mirror the `docs/` tree.

## Recommended Wiki Structure

* Home
* Architecture Notes
* Strategy Research
* AI Experimentation
* Market Data Notes
* Plugin Concepts
* Performance Optimization
* Security Research
* Local Infrastructure
* Trading Psychology Research
* Future Features
* Experimental Ideas

## Page Hierarchy Pattern

Use a shallow structure with clear page names:

* `Architecture Notes`
* `Architecture Notes/Replay Runtime Ideas`
* `Strategy Research/Mean Reversion Candidates`
* `AI Experimentation/Prompt Evaluation 2026 05`

## Naming Conventions

* use title case page names
* start with the domain area
* add time or experiment labels when the topic is fluid
* rename or archive vague pages quickly

## What Belongs In The Wiki

* design brainstorming
* rough comparisons
* vendor notes
* open questions
* prompt experiments
* performance tuning experiments
* early strategy ideas

## What Does Not Belong In The Wiki

* official setup instructions
* canonical API contracts
* current environment variables
* approved security guidance
* final plugin contracts
* release critical operational procedures

## Promotion Rules

Promote Wiki content into `docs/` when:

* the design is accepted
* other contributors now depend on it
* a workflow becomes repeatable
* a research note becomes a product constraint

## Governance Recommendations

* review stale wiki pages every month
* move approved content into `docs/`
* link from the Wiki back to canonical docs when both exist
* date time sensitive pages so old conclusions are obvious
