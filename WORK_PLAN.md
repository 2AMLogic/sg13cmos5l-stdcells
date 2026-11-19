# Work Plan

Roadmap generated from GitHub label state by the Guide triage role.
Only the region between the markers is machine-generated.

<!-- guide:plan-body:start -->
_Generated: 2026-11-19T03:02:00Z (snapshot; compare against live labels)_
## Operator Attention: Merge-Risk-Hold Pileup

Judge-approved PRs under a hold (`loom:blocked` or `loom:operator`) — only a human merge decision is missing.

_None._

## Very Important

`loom:very-important` (one counts per workspace); every stage takes these first.

- **#24**: T1 item 2 (layout): retargeted generator output, committed GDS for the 40 cells on the 8-track SG13CMOS5L row *(held)*

## Important

`loom:important`; taken before unlabelled work.

- **#27**: T1 item 5 (corner verification): Liberty characterization of the 40 cells at the ratified corners with a per-corner timing-margin metric *(held)*
- **#129**: T1 item 5h: decide how item 5 reaches met (5 SS rise arcs exceed the ratified grid-validity bound)

## Ready

Human-approved issues (`loom:issue`) ready for implementation — excluding held (`loom:blocked`/`loom:operator`/`loom:frozen`), `loom:building`, and issues closed by an open `loom:pr` PR (listed under Approved).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#129**: T1 item 5h: decide how item 5 reaches met (5 SS rise arcs exceed the ratified grid-validity bound)

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#224**: spec: propose record 0008 closing the item-5 margin gap by widening the failing cells' PMOS pull-up

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

_None._

## Proposed

Issues carrying `loom:curated`.

- **#6**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#26**: T1 item 4 (LVS clean): klt lvs match of every generated cell against its item-1 netlist *(curated)* *(held)*
- **#28**: T1 item 6 (Monte Carlo): bound not_applicable statement accounting for every ratified row *(curated)* *(held)*
- **#87**: T1 item 5f: cite the three-corner report as item-5 evidence and regenerate the verdict of record *(curated)* *(held)*
- **#129**: T1 item 5h: decide how item 5 reaches met (5 SS rise arcs exceed the ratified grid-validity bound) *(curated)*

## Proposed (Architect / Hermit)

- **#105**: Remove or wire up the vendored sim/harness: 2,155 lines of Python with no experiment, no CI step, and no record *(hermit)* *(held)*
- **#117**: Remove the vendored manifests/design-evidence-tiers.md: a second tiers-doc pin that has drifted from the copy the pinned klt ships (1,053 lines) *(hermit)* *(held)*
- **#134**: Remove the cocotb RTL truth-table harness: test_arcs.py already checks every rtl model against the catalog through iverilog (356 checks, one build, no venv) *(hermit)* *(held)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 1 |
| Important | 2 |
| Ready (`loom:issue`, net of holds/building/merge-pending) | 0 |
| In Progress (`loom:building`) | 1 |
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 0 |
| Curated | 5 |
| Architect / Hermit proposals | 3 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
