# Work Log

Chronological record of merged PRs and closed issues, newest first.
Maintained by the Guide triage role.

### 2026-11-13

- **PR #98**: feat(characterize): FF/1.32V/-40C Liberty for 39 of 40 cells, with coverage check

### 2026-11-12

- **PR #96**: Bump Repo Skills 0.25.10 -> 0.26.1
- **Issue #91** (closed): verification/functional README states ngspice 47 but record reports ngspice 46
- **PR #93**: docs(verification): state ngspice 46 for the TT functional record
- **PR #90**: feat(verification): bit-exact netlist-vs-RTL truth-table check for all 40 cells at TT
- **PR #89**: feat(sim): add per-point timing-margin metric computed from characterized .lib files
- **Issue #83** (closed): T1 item 5b: define and compute the per-point timing-margin metric
- **Issue #82** (closed): T1 item 5a: bit-exact functional check of the 40 cells against rtl/ models
- **PR #81**: feat(sim): generate per-corner klt characterize requests and record an nand2 TT probe
- **PR #78**: feat(sim): record five-corner DC batch run of the reference inverter
- **Issue #4** (closed): PDK and toolchain bring-up: pin SG13CMOS5L, commit an ngspice smoke run and a klt DRC/LVS smoke on a reference cell

### 2026-11-11

- **PR #76**: feat(sim): pin klt 0.9.1 and record five-corner batch transient run

### 2026-11-10

- **Issue #21** (closed): Remove placeholder package.json scripts that always succeed

### 2026-11-07

- **PR #72**: Bump Repo Skills 0.25.1 -> 0.25.10

### 2026-11-06

- **PR #70**: ci: run PDK-free design and RTL checks in a design-rtl job
- **Issue #69** (closed): Run the PDK-free design and RTL checks in CI (netlist/model freshness, truth tables)

### 2026-11-05

- **PR #67**: feat: add JSON form of item 6 statement with drift check
- **PR #66**: feat: attest T1 item 10 repo hygiene and refresh README status
- **Issue #65** (closed): T1 item 10 (repo hygiene): current README status, hygiene inventory, klt signoff --attest 10

### 2026-11-02

- **PR #62**: ci: cite item-9 attestation in manifest and re-check it in CI
- **Issue #31** (closed): T1 item 9 (testbenches shipped): testbench inventory over the smoke and characterization benches, attested with klt signoff --attest 9
- **PR #61**: fix(verification): re-record item 6 spec hash and run its check in CI

### 2026-11-01

- **PR #59**: Bump Repo Skills 0.24.7 -> 0.25.1

### 2026-10-30

- **Issue #23** (closed): T1 item 1 (design sources): transistor-level schematics and derived netlists for the 40-cell combinational set on sg13_lv
- **PR #55**: feat(verification): attest T1 item 1 design sources and declare digital kind
- **Issue #36** (closed): T1 item 1d: item-1 inventory, klt signoff --attest 1, manifest evidence

### 2026-10-29

- **PR #8**: ci: validate JSON evidence and graded klt signoff record
- **Issue #5** (closed): Repo hygiene and CI (T1 item 10): real CI checks, a graded klt signoff manifest, README spec-issue fix

### 2026-10-27

- **PR #51**: build: pin klayout-tools 0.8.0 release and check klt by version
- **Issue #49** (closed): Bump klayout-tools pin dce956c3c399 → 0.8.0
- **PR #48**: refactor: share one strict Liberty-function parser between SPICE and Verilog generators
- **PR #47**: test(sim): verify w/ng semantics and 40 netlists against PDK models
- **PR #42**: feat(design): add netlist generator and 40 derived sg13_lv netlists
- **PR #41**: feat(rtl): generate functional Verilog models from the cell catalog
- **PR #39**: feat(design): ratify 40-cell combinational catalog with count check
- **PR #38**: feat(sim): attest T1 item 9 testbenches with klt signoff inventory
- **PR #37**: feat: add item 6 not_applicable statement with spec hash check
- **Issue #46** (closed): Consolidate duplicate Liberty-function parsers in gen_models.py and gen_netlists.py
- **Issue #44** (closed): Verify generated netlists against the pinned PDK sg13_lv models (w total vs per-finger)
- **Issue #35** (closed): T1 item 1c: generated functional Verilog models for the 40 cells with exhaustive cocotb test
- **Issue #34** (closed): T1 item 1b: committed netlist generator and 40 derived sg13_lv netlists with freshness check
- **Issue #33** (closed): T1 item 1a: ratify the 40-cell combinational list (catalog and decision record)

### 2026-10-21

- **PR #17**: Bump Repo Skills 0.24.3 -> 0.24.7

### 2026-10-18

- **PR #13**: docs: describe the real klt pin in the porting-plan toolchain row
- **PR #12**: docs: record clean-clone setup-env.sh run
- **Issue #11** (closed): spec/porting-plan.md: layout/toolchain.json row still says klt pin is a placeholder

### 2026-10-17

- **PR #10**: feat: pin SG13CMOS5L PDK and toolchain with sim and DRC/LVS smoke evidence
- **PR #9**: docs(spec): ratify SG13CMOS5L target spec and PDK comparison
- **PR #7**: feat: pin sg13g2-stdcells sim harness in reuse.lock.json with porting plan
- **PR #1**: chore(loom): Install Loom 0.19.1181
- **Issue #3** (closed): Port of sg13g2-stdcells: pin the origin's sim harness in reuse.lock.json (adopt or record)
- **Issue #2** (closed): Draft and ratify the target spec
