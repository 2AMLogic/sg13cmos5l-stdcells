# 0006 — Netlist generator pinned upstream; local topology copy retired

- **Status**: accepted
- **Date**: 2026-11-15
- **Issue**: #165
- **Supersedes**: [0003](0003-netlist-generator-local.md)

## Context

0003 landed `design/gen_netlists.py` as a recorded local divergence "until
upstreamed", with the exit condition: "When it lands, pin it in
`reuse.lock.json` and reduce this file to the sizing configuration."
`2AMLogic/sg13g2-stdcells#5` — the PDK-independent generator — landed and is
closed (2026-11-04); the engine is vendored byte-identical at `26935d33`
(`layout/vendor/sg13g2-stdcells/design/gen_netlists.py`, `reuse.lock.json`,
read for issue #151). The local file still carried the second copy of the
topology and of the Liberty-function parser: a standing divergence from the
reuse rule now that a pin exists.

## Decision

Adopt the pinned upstream generator as the one netlist engine and retire the
local copy:

- `design/gen_netlists.py` shrinks to the SG13CMOS5L adapter. It merges
  `design/cells.json` with the `process` sizing block of
  `layout/sg13cmos5l-cells.config.json` — the sizing configuration 0003 kept
  local, which lives in the layout config with a citation per value — into
  the config the engine consumes, and delegates to the vendored engine. The
  CLI is unchanged (`python3 -I design/gen_netlists.py [--check] [--out
  DIR]`), so the item-1 inventory checks, CI and the npm scripts are
  untouched.
- The adapter re-exports the engine's `parse`/`evaluate`: the one shared
  Liberty-function parser (0003 addendum; `rtl/gen_models.py` and, through
  it, `verification/functional/gen_functional.py`'s arc derivation) is now
  the pinned implementation. No second parser remains in the repo.
- The committed 40 netlists are regenerated with the engine. Equivalence was
  measured before the switch: engine output over the merged config differs
  from the previously committed netlists **only** in header line 2 — the
  engine does not emit the "sg13_lv devices" phrase — and this repo adopts
  the upstream header wording rather than diverging the engine over a
  comment phrase. All 40 bodies are byte-identical, and header line 1 is
  byte-identical because the engine's `config_name` parameter carries
  `design/cells.json`.
- The row-fit rule (finger caps + 440 nm rail + 700 nm N-P diffusion-spacing
  reserve inside the 3360 nm row) moves from deleted constants to an assert
  in the adapter, checked against the layout config so the two files cannot
  drift; the `process` block's `_citations` now cite the committed netlists
  and the ratified spec instead of the deleted local constants.
- Item 1 is re-attested over the regenerated netlists and the amended
  inventory description (which names the pinned engine); the manifest's
  item-1 `content_hash` and the signoff record are regenerated in the same
  change, per `manifests/README.md`.

## Consequences

- The topology code is back under the pinned-reference rule: a generator that
  cannot express an SG13CMOS5L need is an upstream bug
  (2AMLogic/sg13g2-stdcells), fixed there, never forked here.
- `design/tests/test_gen_netlists.py` pins the delegation: the vendored
  file's sha256 against its `reuse.lock.json` entry, parser identity, and
  the catalog + process config shape, beside the usual freshness and
  truth-table checks.
- Netlist header line 2 no longer says "sg13_lv devices"; the devices and
  supply are still `sg13_lv_*` at 1.20 V — unchanged and attested.
- If a future SG13CMOS5L need cannot be expressed by the upstream generator,
  that is an upstream change with its own timing; it must not become a local
  fork. A local stopgap would need a new decision record.
