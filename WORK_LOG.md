# Work Log

Chronological record of merged PRs and closed issues, newest first.
Maintained by the Guide triage role.

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
