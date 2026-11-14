# verification

- `item6-not-applicable.md` — T1 item 6 (Monte Carlo) `not_applicable`
  statement, one entry per spec Parameters row, bound to the SHA-256 of
  `spec/target-spec.md`. Checked by `scripts/check_item6_statement.py`.
- `item6-not-applicable.json` — the same per-row table as JSON, the form
  `klt signoff` grades; generated from the markdown with
  `scripts/check_item6_statement.py --write-json`.
- `item1-attest.json` — T1 item 1 (design sources) attestation envelope from
  `klt signoff --attest 1 --inventory design/item1-inventory.json`: 40
  netlists and 40 Verilog models, each with its generator's `--check`.
  That inventory is itself **generated** from `design/cells.json` by
  `design/gen_item1_inventory.py` — do not edit it by hand. Its `--check` runs
  in CI's `design-rtl` job beside the two view generators' own, so a catalog
  edit that leaves the inventory behind fails by name instead of only moving
  this envelope's `content_hash` (issue #144). The generator emits the attested
  bytes exactly, so regenerating it is not a reason to re-attest.
  `scripts/check_signoff.sh`, which CI runs, re-checks it at the klt pin of
  record (`layout/toolchain.json`) along with every other attestation envelope
  the block manifest cites — the list is derived from the manifest, so there is
  no per-item block to add (issue #133). Re-attest after any change to a source
  or derived file, then update the item-1 `content_hash` in
  `manifests/sg13cmos5l-stdcells.json` and regenerate the signoff record; see
  `manifests/README.md`.

See the repo README for scope.
