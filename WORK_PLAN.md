# Work Plan

Roadmap generated from GitHub label state by the Guide triage role.
Only the region between the markers is machine-generated.

<!-- guide:plan-body:start -->
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

_None._

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

_None._

## Important

`loom:important`; taken before unlabelled work.

- **#24**: T1 item 2 (layout): retargeted generator output, committed GDS for the 40 cells on the 8-track SG13CMOS5L row
- **#82**: T1 item 5a: bit-exact functional check of the 40 cells against rtl/ models
- **#84**: T1 item 5c: run klt characterize at TT/1.20 V/25 C for all 40 cells and commit the Liberty

## Ready

Human-approved issues ready for implementation (`loom:issue`).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#82**: T1 item 5a: bit-exact functional check of the 40 cells against rtl/ models
- **#83**: T1 item 5b: define and compute the per-point timing-margin metric
- **#86**: T1 item 5e: run klt characterize at SS/1.08 V/125 C (stretch) and commit the Liberty

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

_None._

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#90**: feat(verification): bit-exact netlist-vs-RTL truth-table check for all 40 cells at TT

## Proposed

Issues carrying `loom:curated`.

- **#6**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#26**: T1 item 4 (LVS clean): klt lvs match of every generated cell against its item-1 netlist *(curated)*
- **#28**: T1 item 6 (Monte Carlo): bound not_applicable statement accounting for every ratified row *(curated)*
- **#82**: T1 item 5a: bit-exact functional check of the 40 cells against rtl/ models *(curated)*
- **#83**: T1 item 5b: define and compute the per-point timing-margin metric *(curated)*
- **#84**: T1 item 5c: run klt characterize at TT/1.20 V/25 C for all 40 cells and commit the Liberty *(curated)*
- **#85**: T1 item 5d: run klt characterize at FF/1.32 V/-40 C (stretch) and commit the Liberty *(curated)*
- **#86**: T1 item 5e: run klt characterize at SS/1.08 V/125 C (stretch) and commit the Liberty *(curated)*

## Proposed (Architect / Hermit)

_None._

## Epics



_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 0 |
| Important | 3 |
| Ready (`loom:issue`) | 0 |
| In Progress (`loom:building`) | 3 |
| PRs awaiting review | 0 |
| Approved PRs awaiting merge | 1 |
| Curated | 8 |
| Architect / Hermit proposals | 0 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
