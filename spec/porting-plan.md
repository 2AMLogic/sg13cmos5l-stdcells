# Porting plan: sg13g2-stdcells -> sg13cmos5l-stdcells

Origin: `2AMLogic/sg13g2-stdcells`, default branch `main`. This plan decides no
spec parameter (those belong to #2) and chooses no PDK pin (that belongs to #4).

`/reuse.lock.json` carries **one `imports[]` element per pinned commit**, and
there are now two:

| Commit | Read at | Covers |
|---|---|---|
| `f450813c6a5eecf3cf67aaf899db90d11f4ee68c` | 2026-10-17 | the characterization harness, `sim/harness/` (10 files) |
| `26935d337bdacf8f46ed59678e4d0c9725965408` | 2026-11-14 | the cell layout generator, `layout/vendor/sg13g2-stdcells/` (2 files) — issue #151 |

The second pin re-reads the origin at a later commit; it does **not** re-pin the
harness, whose element is untouched. Rows below are tagged with the pin they
were read at where it matters.

## Per-file disposition

| Origin file | Disposition | Local path | Notes |
|---|---|---|---|
| `sim/harness/__init__.py` | adopted | `sim/harness/__init__.py` | vendored, byte-identical, sha256 in lock |
| `sim/harness/cli.py` | adopted | `sim/harness/cli.py` | vendored, byte-identical |
| `sim/harness/corners.py` | adopted | `sim/harness/corners.py` | vendored, byte-identical |
| `sim/harness/evidence.py` | adopted | `sim/harness/evidence.py` | vendored, byte-identical |
| `sim/harness/pdk.py` | adopted | `sim/harness/pdk.py` | vendored, byte-identical; PDK comes from a block-authored `sim/pdk.json` (#4) |
| `sim/harness/report.py` | adopted | `sim/harness/report.py` | vendored, byte-identical |
| `sim/harness/runner.py` | adopted | `sim/harness/runner.py` | vendored, byte-identical |
| `sim/harness/testbench.py` | adopted | `sim/harness/testbench.py` | vendored, byte-identical |
| `sim/harness/toolchain.py` | adopted | `sim/harness/toolchain.py` | vendored, byte-identical |
| `sim/harness/README.md` | adopted | `sim/harness/README.md` | vendored, byte-identical |
| `sim/README.md` | not applicable | `sim/README.md` | this repo keeps its own placeholder README |
| `layout/README.md` | not applicable | `layout/README.md` | this repo keeps its own README |
| `layout/toolchain.json` | diverged (template only) | `layout/toolchain.json` | taken as a template, not vendored, so it is not in the lock. This repo's copy carries its own `klt` pin (`klt.commit`, `klt.install_spec`, plus `klt.klt_required_commands`), set from the first `klt` commit verified on this PDK (issue #4). The origin's pin is not carried over. No decision record: a template is not a divergence from a shared file. |
| `layout/gen_layouts.py` | adopted | `layout/vendor/sg13g2-stdcells/layout/gen_layouts.py` | vendored, byte-identical at `26935d33`. Under `vendor/` because the file resolves its netlist-generator import relative to its own grandparent, so the upstream `layout/` + `design/` shape has to be preserved under one root — and that root cannot be the repo root without overwriting this repo's local `design/gen_netlists.py`. Driven by this repo's `layout/sg13cmos5l-cells.config.json`. |
| `design/gen_netlists.py` | adopted (second copy) | `layout/vendor/sg13g2-stdcells/design/gen_netlists.py` | vendored, byte-identical at `26935d33`, **imported only by the vendored `gen_layouts.py`**. This does not replace `/design/gen_netlists.py`, which stays the local divergence of decision record 0003 (not config-driven, no `validate`/`PROCESS_KEYS`, and imported by `rtl/gen_models.py`). The two copies coexist deliberately; replacing the local one with the upstream one is 0003's follow-up, not this row. |
| `layout/example_config.json` | not applicable (template only) | `layout/sg13cmos5l-cells.config.json` | read as a template, not vendored, so it is not in the lock. Every layer number and rule value in this repo's config was read from the SG13CMOS5L PDK at the `/sim/pdk.json` pin and carries its citation in `layout._citations`; `rail_width_nm` is this repo's ratified 440 nm, not the origin example's 160 nm. Same treatment as `layout/toolchain.json`. |

No vendored file differs from upstream, so no decision record is needed and
no lock entry carries `"diverged"`.

## Decisions

- **Vendored in place, not under `sim/harness/common/`.** The origin documents
  `python -m sim.harness`-style entry points, and a `common/` subdirectory
  would need them rewritten, which would create a divergence for no gain.
- **Lock format.** `reuse.lock.json` follows the `imports[]` shape
  `{from, commit, mode, files:[{upstream, local, sha256}]}` used by
  `2AMLogic/gf180-usb2-phy/reuse.lock.json` for `mode: "vendored"`. The
  issue's two named consumers (`gf180-bandgap`, `sg13g2-bandgap`) carry only
  `in_tree` entries, so they do not show this shape. No schema or validator
  for it was found in `klayout-tools`.
- **Cell layout generator: pinned 2026-11-14 (issue #151).** It landed upstream
  after the first pin, so it got its own `imports[]` element rather than extra
  files on the harness element — one element per commit. The generator retargets
  to SG13CMOS5L by configuration alone and places `s5l_inv_1` on the 3.36 um
  row; evidence and the margin budget are in `layout/README.md`.
- **The origin's `nsd` layer is required, not optional.** The generator lists
  `nsd` in `OPTIONAL_LAYERS` but its placer refuses without it (the tap is drawn
  as a well tie, `activ & nsd`). The config carries `nsd` as `7/0`. The
  validator/placer disagreement is an upstream defect
  (2AMLogic/sg13g2-stdcells#80), never a local edit to a vendored file.

## Gaps found in the origin

- `sim/harness/` has no `__main__.py`, so the documented
  `python -m sim.harness <cmd>` fails. The working form is
  `python -m sim.harness.cli <cmd>`. Filed as
  2AMLogic/sg13g2-stdcells#4; the local copy stays byte-identical to the pin
  until upstream fixes it.
- `layout/gen_layouts.py` lists `nsd` in `OPTIONAL_LAYERS`, so `validate_layout`
  accepts a config without it, but the tap code requires it unconditionally — a
  config the validator passes then fails at exit 3 (`cannot place`) where exit 2
  (`invalid config`) is the honest code. Filed as
  2AMLogic/sg13g2-stdcells#80; the local copy stays byte-identical to the pin
  until upstream fixes it.

## Verification status

- [x] `reuse.lock.json` pins a full 40-hex commit reachable on the origin's
  default branch; every vendored file's `sha256` equals the upstream blob at
  that commit and the local copy. Re-verified for the `26935d33` element on
  2026-11-14 from an independent clone (`git merge-base --is-ancestor` against
  `origin/main`, then `git show <commit>:<path> | sha256sum` for both files).
  No automated gate covers this: `scripts/check_json.py` parses tracked JSON, it
  hashes nothing, so re-check it by hand whenever a pin moves.
- [x] The vendored layout generator runs on this repo's config: writes
  `layout/gds/s5l_inv_1.gds`, `--check` exits 0, output byte-identical across
  independent runs (`npm run check:layout`, wired into `check:ci`).
- [x] `python -c "import sim.harness"` and `python -m sim.harness.cli list`
  run on the vendored copy (no PDK or ngspice needed).
- [ ] Harness `selftest`: **deferred to #4.** It needs an experiment under
  `sim/<experiment>/`, `sim/pdk.json` and a working ngspice plus PDK, which
  are #4's deliverables. Tick this when #4 provides them.
