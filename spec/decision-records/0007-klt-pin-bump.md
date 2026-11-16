# 0007 — Characterization klt pin moved to the 0.9.2 release

- **Status**: accepted
- **Date**: 2026-11-15
- **Issue**: #109
- **Supersedes**: the `klayout-tools==0.9.1` reference in [0005](0005-timing-margin-spec-row.md) §"pinned grader" — by addition. 0005 is ratified and is not edited; wherever 0005 says "the pinned grader (`klayout-tools==0.9.1`)", read the pin of record, `layout/toolchain.json`, which this record moves to `klayout-tools==0.9.2`. The grader behaviour 0005 describes is unchanged: the `timing_margin` spec-row mechanics it cites are the same code at 0.9.2.

## Context

`layout/toolchain.json` pinned `klayout-tools==0.9.1` (tag v0.9.1, commit
`4d0d29be4fd9`), but every recorded characterization run was made with an
unreleased `0.9.2.dev*` host build, because `klt characterize`'s
`--split-grid`, `--wait-for-capacity` and `--resume` — the flags the
five-corner and multi-corner runs actually use (`--split-grid` is
klayout-tools#5410) — all landed after 0.9.1. Each provenance record names its
exact klt commit, so the runs are traceable; they are just not runs of the
pinned tool, and `sim/characterize/README.md`'s documented invocation
(`source .cache/env.sh` then `klt characterize …`) could not run at the pin,
because `scripts/setup-env.sh` installs the pin into the checkout venv.

klayout-tools 0.9.2 (tag v0.9.2, commit `046ba74652fc`) is the first PyPI
release carrying all three flags, so the pin can move and the documented
commands become true. The alternative — pinning a git build of a host dev
tree — is rejected again for the reason `_comment` already records from issue
#49: a git build reports a dev version that does not satisfy `==X.Y.Z`
(klayout-tools#2823), and `install_spec` is a PyPI spec.

## Decision

Bump the characterization klt pin of record to the 0.9.2 release:

- `layout/toolchain.json`: `klt.commit` → `046ba74652fc096bd97071fc3237f7159dd40183`,
  `klt.install_spec` → `klayout-tools==0.9.2`, `klt.version_reported` →
  `0.9.2`, `klt_fetch_scripts.base_url` at the new commit. The four fetch
  scripts were re-hashed at the new commit and are byte-identical to the
  0.9.1 ones, so their sha256 values are unchanged (as at the 0.8.0 → 0.9.1
  bump). The appended `_comment` paragraph records the same.
- `sim/attest/item9.inventory.json`'s `pins.tools.klt` follows the pin of
  record, item 9 is re-attested at the new pin, and the signoff record of
  `manifests/sg13cmos5l-stdcells.signoff.json` is regenerated — the chain
  `manifests/README.md` prescribes for a tool-pin bump. The regenerated
  record moves only the `build` block (version, commit, tag,
  `grading_ruleset_id`) and the item-9 inventory hashes: `t1_met_count`
  stays 3 of 11 and no item's `status` moves.
- No recorded evidence is regenerated or edited. The characterization
  provenance records under `sim/characterize/records/` and the smoke records
  under `sim/smoke/records/` are append-only; the runs they recorded used
  `0.9.2.dev*` host builds and say so, and that stays true. A re-run at the
  new pin is new evidence under its own issue, not an edit here.

## Consequences

- The documented characterization invocation (`source .cache/env.sh` +
  `klt characterize`) now runs the pin of record itself; no `uvx --from`
  second invocation style is introduced, because a second pin would drift.
- `sim/characterize/README.md`, `sim/smoke/README.md`, `ROADMAP.md` and
  `manifests/README.md` statements that named 0.9.1 as *the* pin are
  corrected in the same change; inside a run's own provenance prose the pin
  is date-stamped as the pin at the time of that run, not rewritten.
- The pin of record stays the one version literal in the repo: no klt
  version literal is introduced under `scripts/` or `.github/`
  (`manifests/item-10-inventory.json`'s `no-hardcoded-klt-version` check
  keeps it that way).
- A future klt pin bump that changes the netlist-text normalization surfaces
  first in `check_signoff.sh`'s `check_netlist_identities`; at 0.9.2 it
  recomputes clean for all three functional records.
