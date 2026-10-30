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
  `design/item1-inventory.json`. The citation's `content_hash` is the
  inventory's sha256 (the envelope's `provenance.input.content_hash`), not the
  envelope file's. Re-attest after any change to a source, derived file or the
  inventory, then update the hash here and regenerate the signoff record.

## Regenerate the signoff record

klt is pinned to `0.7.0` (in `scripts/check_signoff.sh`). Change the manifest,
the tiers doc, or the pin, then regenerate with the same version:

```
uvx --from "klayout-tools==0.7.0" klt signoff \
    --manifest manifests/sg13cmos5l-stdcells.json \
    --tiers-doc manifests/design-evidence-tiers.md \
    --format json > manifests/sg13cmos5l-stdcells.signoff.json
```

Exit status 3 (grader ran, some T1 item unmet) is expected until the evidence
map is filled in.
