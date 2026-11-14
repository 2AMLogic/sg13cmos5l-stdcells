# Block manifest and signoff record

- `sg13cmos5l-stdcells.json`: the block manifest (`block`, `kind`, `evidence`).
  Each evidence item is added by the issue that
  produces it.
- `sg13cmos5l-stdcells.signoff.json`: the committed `klt signoff` output, the
  tier verdict of record. CI regenerates it and fails on any difference.
- `design-evidence-tiers.md`: the T1 checklist, vendored from
  `https://github.com/2AMLogic/klayout-tools/blob/267ea83a0510bcb61d2956058095201c0f481ff7/docs/design-evidence-tiers.md`
  (commit `267ea83a0510bcb61d2956058095201c0f481ff7`).

## `kind`

`klt signoff` requires `kind` to be one of `analog`, `digital`, `mixed-signal`.
The block declares `digital` (full-custom sub-case), per
`spec/decision-records/0004-block-kind-digital.md`. A revision of `kind` goes
through a decision record and regenerates the signoff output in the same PR.

## Evidence

- Item 1: `verification/item1-attest.json`, produced from
  `design/item1-inventory.json` with `klt signoff --attest 1`. The citation's
  `content_hash` is the envelope's `provenance.input.content_hash`, not the
  envelope file's — for item 1 that is one hash over the inventory *and* every
  source and derived file it lists (84 paths at klt 0.9.1; a pre-0.9 klt hashed
  the inventory file alone, so the committed envelope reported `drifted` under
  the pin until issue #133 re-attested it). A change to any netlist or model
  therefore moves this hash. Re-attest after any change to a source, derived
  file or the inventory, then update the hash here and regenerate the signoff
  record. `scripts/check_signoff.sh` re-checks the envelope at the pin.

- Item 9: `sim/attest/item9.envelope.json`, produced from
  `sim/attest/item9.inventory.json` with `klt signoff --attest 9`. As for
  item 1, `content_hash` is the envelope's `provenance.input.content_hash` —
  for this item the inventory's own sha256. `scripts/check_signoff.sh`, which
  CI runs, re-runs `klt signoff --attest 9 --inventory ... --check ...` on it at
  the pin in `layout/toolchain.json`. `--attest` is absent from klt 0.7.0, so
  that pin cannot go below 0.8.0.
  The inventory's `pins` block copies this repo's tool and PDK pins, and klt's
  own `pin` check only verifies that the block is present and well formed,
  never what it says -- so the copied klt commit drifted across two pin bumps
  with no gate noticing (issue #131). `check_attest_pins` in
  `scripts/check_signoff.sh` compares every copied value with the file that
  owns it (`layout/toolchain.json`, `sim/toolchain.json`, `sim/pdk.json`)
  before any other check runs, and `scripts/test_check_signoff.sh` is its
  self-test. A tool or PDK pin bump is therefore a two-file change: bump the
  pin of record, then bring the inventory with it and re-attest item 9.

- Item 10: `manifests/evidence/item-10-repo-hygiene.json`, produced from
  `manifests/item-10-inventory.json` with `klt signoff --attest 10`. As for
  item 9, `content_hash` is the inventory's sha256. The inventory lists
  the hygiene files (README, LICENSE, CI workflow, check scripts) and the
  audit commands (README has a Reproduce section and names `npm run check:ci`,
  CI runs `scripts/check_signoff.sh`, that script's own derivation of the
  envelopes to re-check includes item 10, `scripts/check_json.py` passes, no
  klt *or* cocotb version literal is left under `scripts/` or `.github/`, and
  the CI workflow reads the cocotb pin from `rtl/toolchain.json`). The two
  cocotb checks are the enforcement behind issue #119: a one-pin-of-record
  rule that only lives in prose is a rule that drifts back, as the klt literal
  did (issue #112).
  `scripts/check_signoff.sh` re-runs
  `klt signoff --attest 10 --inventory ... --check ...` on it.
  Its `attest_envelopes` derives that list — item, inventory and envelope — from
  this manifest and from each envelope's own `t1_item` and `source`, so the gate
  re-checks exactly the envelopes the manifest cites. It used to be one
  hand-copied block per item, and item 1 never got one: the only cited envelope
  no gate re-checked was the one that had drifted (issue #133).
  Re-attest after any change to the README, LICENSE, CI workflow or check
  scripts, then update the hash and regenerate the signoff record.

- Item 5: cites `verification/functional/records/corners.report.json`, the
  three-corner timing-arc `klt sim` report of issue #120 (**SIMULATED**, never
  measured). The citation's `content_hash` is the report's
  `provenance.input.content_hash` — the netlist's sha256 — **not** the sha256 of
  the report file; citing the file's own hash grades `stale_evidence`.

  The entry also declares the one spec row this block's full-custom digital
  sub-case needs, ratified by
  [decision record 0005](../spec/decision-records/0005-timing-margin-spec-row.md):

  - top-level `spec_rows` `"5"`: `t_stage_delay_grid_bound`, `timing_margin:
    true`, ratified (the default). Without a `timing_margin` row a `sim`-only
    item 5 grades `unmet` / `timing_margin_missing`.
  - the evidence entry's own `rows`: `["t_stage_delay_grid_bound"]`, naming the
    row this citation carries. It does not change the grade, but it is what
    sorts the row into `failed_rows` rather than `uncovered_rows` when the
    citation fails — i.e. it records that the row *was* measured and came back
    over the bound, instead of reading as though nothing covered it.

  **The verdict of record reads `unmet`, reason `check_failed`** — not `met`,
  and no longer `no_limits_checked`. Blocker: `sim__corner__failed_count: 1`.
  `failed_rows: ["t_stage_delay_grid_bound"]`, `uncovered_rows: []`,
  `declared_gaps: []`, `unratified_rows: []` — the timing-margin rule itself is
  satisfied, and only the measurement verdict blocks the item.

  Coverage actually cited, as the report declares it:
  - Three corners, all three ratified Liberty corners, each simulated:
    `tt/1.200V/25C` **pass**, `ff/1.320V/-40C` **pass**, `ss/1.080V/125C`
    **fail**.
  - 212 arc delays per corner (106 timing arcs of all 40 cells, rise and fall),
    636 in total. All 212 declared measurements carry `limits`, and all 212 are
    limit-checked (`coverage.measurements_with_limits` = 212,
    `unrecognized_limit_keys: []`). Zero declared arc gaps.
  - One grid point per corner — the ratified characterization grid's worst
    point, input slew 2.5074 ns and output load 0.3 pF. Stage delay is monotonic
    in both, so a pass there carries the bound over the whole 7 x 7 grid.
  - **The recorded fail: 5 of the 636 arc delays exceed the 2.5074 ns bound**,
    all of them rise arcs at SS / 1.08 V / 125 C: `s5l_nand4_1` `Y<-D`
    (2.5622 ns, margin **-0.0548 ns**, the least), `s5l_nand4_1` `Y<-C`
    (-0.0319 ns), `s5l_nand3_1` `Y<-C` (-0.0116 ns), `s5l_nand3b_1` `Y<-C`
    (-0.0116 ns), `s5l_nand4_1` `Y<-B` (-0.0077 ns). These are the same five
    arcs, with the same least margin, that `sim/characterize/margin.py`
    independently records over the characterized Liberty. They are recorded as
    a fail and left as they are; nothing was retuned to make them pass.
  - The bound is a **grid-validity** bound, not a timing-closure budget or a
    delay target (decision record 0005).

  Moving item 5 to `met` from here needs either a ratified delay budget or a
  change to the characterization grid row — each its own decision record, and
  neither an agent's call. That ruling is tracked in
  [#129](https://github.com/2AMLogic/sg13cmos5l-stdcells/issues/129). It is out
  of scope for this citation, which records the verdict the evidence on main
  actually supports.

  Earlier coverage note, now superseded: until 2026-11-13 this item cited
  `tt.report.json` (TT only, no limited measurement) and graded `unmet` /
  `no_limits_checked`.

## Regenerate the signoff record

klt has one pin of record, `klt.install_spec` in `layout/toolchain.json`.
`scripts/check_signoff.sh` reads it, so there is no second version to keep in
step by hand (issue #112; the hand-synced copy had drifted). Change the
manifest, the tiers doc, or the pin, then regenerate with the pinned klt and
commit the result in the same PR:

```
scripts/check_signoff.sh --regenerate
```

Run `scripts/check_signoff.sh` (no argument, the same command CI runs) to check
the committed record and re-check every attestation envelope this manifest
cites (items 1, 9 and 10 today). Exit status 3 from `klt signoff` itself
(grader ran, some T1 item unmet) is expected until the evidence map is filled
in; the script treats it as success and compares the output.
