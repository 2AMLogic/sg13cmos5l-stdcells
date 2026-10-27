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

- **#4**: PDK and toolchain bring-up: pin SG13CMOS5L, commit an ngspice smoke run and a klt DRC/LVS smoke on a reference cell
- **#34**: T1 item 1b: committed netlist generator and 40 derived sg13_lv netlists with freshness check
- **#35**: T1 item 1c: generated functional Verilog models for the 40 cells with exhaustive cocotb test

## Ready

Human-approved issues ready for implementation (`loom:issue`).

_None._

## In Progress

Issues currently being built (`loom:building`).

- **#5**: Repo hygiene and CI (T1 item 10): real CI checks, a graded klt signoff manifest, README spec-issue fix
- **#34**: T1 item 1b: committed netlist generator and 40 derived sg13_lv netlists with freshness check
- **#35**: T1 item 1c: generated functional Verilog models for the 40 cells with exhaustive cocotb test

## PRs Awaiting Review

PRs waiting on Judge (`loom:review-requested`).

- **#41**: feat(rtl): generate functional Verilog models from the cell catalog

## Approved (Awaiting Merge)

PRs that passed review and are queued for Champion auto-merge (`loom:pr`).

- **#8**: ci: validate JSON evidence and graded klt signoff record

## Proposed

Issues carrying `loom:curated`.

- **#4**: PDK and toolchain bring-up: pin SG13CMOS5L, commit an ngspice smoke run and a klt DRC/LVS smoke on a reference cell *(curated)*
- **#5**: Repo hygiene and CI (T1 item 10): real CI checks, a graded klt signoff manifest, README spec-issue fix *(curated)*
- **#6**: Track the gap to T1 (klayout-tools design-evidence-tiers.md) *(curated)*
- **#28**: T1 item 6 (Monte Carlo): bound not_applicable statement accounting for every ratified row *(curated)*
- **#31**: T1 item 9 (testbenches shipped): testbench inventory over the smoke and characterization benches, attested with klt signoff --attest 9 *(curated)*
- **#34**: T1 item 1b: committed netlist generator and 40 derived sg13_lv netlists with freshness check *(curated)*
- **#35**: T1 item 1c: generated functional Verilog models for the 40 cells with exhaustive cocotb test *(curated)*

## Proposed (Architect / Hermit)



- **#21**: Remove placeholder package.json scripts that always succeed *(hermit)*

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
| PRs awaiting review | 1 |
| Approved PRs awaiting merge | 1 |
| Curated | 7 |
| Architect / Hermit proposals | 1 |
| Active epics | 0 |
<!-- guide:plan-body:end -->
