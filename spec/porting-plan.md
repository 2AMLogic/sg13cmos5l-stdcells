# Porting plan: sg13g2-stdcells -> sg13cmos5l-stdcells

Origin: `2AMLogic/sg13g2-stdcells`, read at commit
`f450813c6a5eecf3cf67aaf899db90d11f4ee68c` (default branch `main`).
That commit is the one pinned in `/reuse.lock.json`. This plan decides no spec
parameter (those belong to #2) and chooses no PDK pin (that belongs to #4).

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
- **No cell generators upstream yet.** They get their own lock entry when
  they land.

## Gaps found in the origin

- `sim/harness/` has no `__main__.py`, so the documented
  `python -m sim.harness <cmd>` fails. The working form is
  `python -m sim.harness.cli <cmd>`. Filed as
  2AMLogic/sg13g2-stdcells#4; the local copy stays byte-identical to the pin
  until upstream fixes it.

## Verification status

- [x] `reuse.lock.json` pins a full 40-hex commit reachable on the origin's
  default branch; every vendored file's `sha256` equals the upstream blob at
  that commit and the local copy.
- [x] `python -c "import sim.harness"` and `python -m sim.harness.cli list`
  run on the vendored copy (no PDK or ngspice needed).
- [ ] Harness `selftest`: **deferred to #4.** It needs an experiment under
  `sim/<experiment>/`, `sim/pdk.json` and a working ngspice plus PDK, which
  are #4's deliverables. Tick this when #4 provides them.
