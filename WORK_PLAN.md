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

- **#129**: T1 item 5h: decide how item 5 reaches met (5 SS rise arcs exceed the ratified grid-validity bound)
- **#151**: Pin the sg13g2-stdcells generators in reuse.lock.json and record a one-cell SG13CMOS5L layout probe

## Ready

Human-approved issues ready for implementation (`loom:issue`).

- **#148**: Commit the arc-state negative controls, and share one trigger-edge helper between the deck and its test

## In Progress

Issues currently being built (`loom:building`).

- **#87**: T1 item 5f: cite the three-corner report as item-5 evidence and regenerate the verdict of record
- **#116**: Wire up or remove the self-tests and --check freshness modes that no gate runs (4 test files, 240 lines, absent from CI and check:ci)
- **#144**: Generate design/item1-inventory.json from design/cells.json: 960 of its 973 lines are two entries repeated 40x each
- **#151**: Pin the sg13g2-stdcells generators in reuse.lock.json and record a one-cell SG13CMOS5L layout probe

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#130**: ci: gate the characterization self-tests, request freshness and the functional compare
- **#136**: evidence: cite the three-corner report for T1 item 5 and regenerate the verdict
- **#150**: docs: roadmap as of 2026-11-13
- **#154**: feat: pin the origin layout generator and place s5l_inv_1 on the 3.36 um row

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#147**: feat(design): generate the item-1 attestation inventory from the cell catalog

## Proposed

Issues carrying `loom:curated`.

- **#6**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#26**: T1 item 4 (LVS clean): klt lvs match of every generated cell against its item-1 netlist *(curated)*
- **#28**: T1 item 6 (Monte Carlo): bound not_applicable statement accounting for every ratified row *(curated)*
- **#87**: T1 item 5f: cite the three-corner report as item-5 evidence and regenerate the verdict of record *(curated)*
- **#148**: Commit the arc-state negative controls, and share one trigger-edge helper between the deck and its test *(curated)*
- **#151**: Pin the sg13g2-stdcells generators in reuse.lock.json and record a one-cell SG13CMOS5L layout probe *(curated)*

## Proposed (Architect / Hermit)

- **#105**: Remove or wire up the vendored sim/harness: 2,155 lines of Python with no experiment, no CI step, and no record *(hermit)*
- **#117**: Remove the vendored manifests/design-evidence-tiers.md: a second tiers-doc pin that has drifted from the copy the pinned klt ships (1,053 lines) *(hermit)*
- **#134**: Remove the cocotb RTL truth-table harness: test_arcs.py already checks every rtl model against the catalog through iverilog (356 checks, one build, no venv) *(hermit)*
- **#145**: Deduplicate the PDK model/OSDI literals in the klt request generators *(hermit)*

## Epics

_None._

## Backlog Balance

| Bucket | Count |
|------|-------|
| Operator merge-risk holds | 0 |
| Very important | 1 |
| Important | 2 |
| Ready (`loom:issue`) | 1 |
| In Progress (`loom:building`) | 4 |
| PRs awaiting review | 4 |
| Approved PRs awaiting merge | 1 |
| Curated | 6 |
| Architect / Hermit proposals | 4 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
