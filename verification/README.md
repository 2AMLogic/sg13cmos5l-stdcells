# verification

- `item6-not-applicable.md` — T1 item 6 (Monte Carlo) `not_applicable`
  statement, one entry per spec Parameters row, bound to the SHA-256 of
  `spec/target-spec.md`. Checked by `scripts/check_item6_statement.py`.
- `item1-attest.json` — T1 item 1 (design sources) attestation envelope from
  `klt signoff --attest 1 --inventory design/item1-inventory.json`: 40
  netlists and 40 Verilog models, each with its generator's `--check`. Verify
  with `klt signoff --attest 1 --inventory design/item1-inventory.json --check
  verification/item1-attest.json`. The `--attest` flag is newer than the pinned
  klt 0.7.0 (which still grades the envelope); produce and check it with a
  current `uvx --from klayout-tools klt`.

See the repo README for scope.
