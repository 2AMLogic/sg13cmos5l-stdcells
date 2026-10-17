# sg13cmos5l-stdcells — agent instructions

Open-source canary block: an 8-track standard-cell library on IHP
SG13CMOS5L, designed and verified by AI agents. A **port** of
`sg13g2-stdcells`, and **mixed-signal** in the sense that matters here —
transistor-level cells characterized into digital views — so both flows
apply.

- **PDK**: IHP SG13CMOS5L (open PDK, IHP-GmbH/IHP-Open-PDK, `ihp-sg13cmos5l`).
  Analog: xschem + ngspice for per-cell characterization. Digital: cocotb +
  Icarus, Yosys, OpenROAD for the functional models and the synthesis
  benchmark. Layout, DRC, and LVS through klayout-tools (`klt`).
- **The metal stack is the point, and the risk.** SG13CMOS5L is CMOS-only
  with a shorter metal stack than SG13G2. Pin access, the routing grid, the
  rail strategy, and the benchmark's routability all move with that stack.
  Establish what the two PDKs share — devices, Metal1 rules, row-height
  constraints — from the PDK documentation before carrying any origin
  decision over. Expect `klt` and the deck to be least exercised on this PDK.
- **The PDK is the variable, not the design.** Start from `sg13g2-stdcells`'
  spec and decision records, not from a blank page. Anything that breaks here
  is assumed to be the PDK, the deck, or the tools before it is assumed to be
  the cell. Departures from the origin go through decision records.
- **Scope discipline — the generators are designed once.** Under the fleet's reuse
  rule (a block is designed once), `sg13g2-stdcells` is the master of the PDK-independent material: cell
  generators, characterization harness mechanics, benchmark scripts. Take
  them by a pinned reference (`reuse.lock.json`), never by a fork. A
  generator that cannot express an SG13CMOS5L rule is a bug to fix upstream
  in `sg13g2-stdcells` first; a local divergence needs a decision record.
  What this repo owns is the SG13CMOS5L configuration, the cells it produces,
  their views, and their evidence.
- **A library is a generator, not a block.** Do not hand-draw a cell that
  differs from another only by drive strength or input count. If it cannot be
  generated, the generator is the bug.
- **Benchmarks compare like with like.** The baseline is the PDK's own
  `sg13cmos5l_stdcell`, through the same open flow on the same designs. Never
  compare against SG13G2 numbers, the origin repo's numbers, or any
  externally published library result as if it were a result of this repo.
- **Friction protocol (the canary's job)**: every time klayout-tools is
  awkward, missing a capability, or wrong for what you need, file an issue at
  `2AMLogic/klayout-tools` describing the tool gap generically — that tracker
  is scoped to the tool, so keep design-specific detail out of it and describe
  the gap, not the design.
- **Verification is the product**: no claim without a testbench. PVT corners
  on every recorded characterization result; recorded results are
  append-only evidence. A simulated number is never called measured.
- Spec changes go through `spec/` with a decision record; agents do not relax
  the ratified spec to make results pass.
