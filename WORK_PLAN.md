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
- **#120**: T1 item 5g: record a limit-checked corner-matrix klt sim report with a per-corner timing-margin measurement

## Ready

Human-approved issues ready for implementation (`loom:issue`).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#120**: T1 item 5g: record a limit-checked corner-matrix klt sim report with a per-corner timing-margin measurement

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

_None._

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#6**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#26**: T1 item 4 (LVS clean): klt lvs match of every generated cell against its item-1 netlist *(curated)*
- **#28**: T1 item 6 (Monte Carlo): bound not_applicable statement accounting for every ratified row *(curated)*
- **#120**: T1 item 5g: record a limit-checked corner-matrix klt sim report with a per-corner timing-margin measurement *(curated)*

## Proposed (Architect / Hermit)

- **#105**: Remove or wire up the vendored sim/harness: 2,155 lines of Python with no experiment, no CI step, and no record *(hermit)*
- **#116**: Wire up or remove the self-tests and --check freshness modes that no gate runs (4 test files, 240 lines, absent from CI and check:ci) *(hermit)*
- **#117**: Remove the vendored manifests/design-evidence-tiers.md: a second tiers-doc pin that has drifted from the copy the pinned klt ships (1,053 lines) *(hermit)*
- **#119**: Unify the three .venv recipes and give cocotb one pin of record (npm run check:ci fails on a setup-env.sh checkout) *(hermit)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 0 |
| Important | 2 |
| Ready (`loom:issue`) | 0 |
| In Progress (`loom:building`) | 1 |
| PRs awaiting review | 0 |
| Approved PRs awaiting merge | 0 |
| Curated | 4 |
| Architect / Hermit proposals | 4 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
