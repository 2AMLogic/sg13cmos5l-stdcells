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

- Item 5: cites `verification/functional/records/tt.report.json`, the TT /
  1.20 V / 25 C `klt sim` functional report (all 40 cells, SIMULATED), by its
  sha256. **The verdict of record reads `unmet` (`no_limits_checked`), not
  `met`.** Coverage as of this citation:
  - TT Liberty: all 40 cells (`sim/characterize/records/s5l_tt_1p20v_25c.lib`).
  - FF / 1.32 V / -40 C Liberty: 39 of 40 cells (`s5l_mux4_1` timed out); partial.
  - SS Liberty: none recorded.
  - Timing-margin code: `sim/characterize/margin.py`; no margin table has been
    recorded over the 40-cell TT library yet.
  - Functional report: TT only, 40/40 cells pass.
  The cited `klt sim` report carries no limited measurement, so klt grades it
  unmet: klt 0.8.0 did, and the klt 0.9.1 record committed on 2026-11-13 does
  too. Turning item 5 `met` needs a corner-matrix report whose
  limits are checked (FF and SS evidence plus the margin metric); that is
  evidence production, out of scope for the citation step.

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
