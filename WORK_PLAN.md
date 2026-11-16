# Work Plan

Roadmap generated from GitHub label state by the Guide triage role.
Only the region between the markers is machine-generated.

<!-- guide:plan-body:start -->
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

_None._

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#24**: T1 item 2 (layout): retargeted generator output, committed GDS for the 40 cells on the 8-track SG13CMOS5L row

## Important

`loom:important`; taken before unlabelled work.

- **#27**: T1 item 5 (corner verification): Liberty characterization of the 40 cells at the ratified corners with a per-corner timing-margin metric
- **#129**: T1 item 5h: decide how item 5 reaches met (5 SS rise arcs exceed the ratified grid-validity bound)

## Ready

Human-approved issues ready for implementation (`loom:issue`).

_None._

## In Progress

Issues currently being built (`loom:building`).

_None._

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
- **#87**: T1 item 5f: cite the three-corner report as item-5 evidence and regenerate the verdict of record *(curated)*

## Proposed (Architect / Hermit)

- **#105**: Remove or wire up the vendored sim/harness: 2,155 lines of Python with no experiment, no CI step, and no record *(hermit)*
- **#117**: Remove the vendored manifests/design-evidence-tiers.md: a second tiers-doc pin that has drifted from the copy the pinned klt ships (1,053 lines) *(hermit)*
- **#134**: Remove the cocotb RTL truth-table harness: test_arcs.py already checks every rtl model against the catalog through iverilog (356 checks, one build, no venv) *(hermit)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 1 |
| Important | 2 |
| Ready (`loom:issue`) | 0 |
| In Progress (`loom:building`) | 0 |
| PRs awaiting review | 0 |
| Approved PRs awaiting merge | 0 |
| Curated | 4 |
| Architect / Hermit proposals | 3 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
