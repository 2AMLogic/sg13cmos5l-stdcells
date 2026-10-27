# `scripts/setup-env.sh` at the klt 0.8.0 pin, 2026-10-27

Append-only evidence for issue #49. Environment bring-up facts only; no
simulation or measurement is claimed.

## Setup

- Worktree checkout of branch `feature/issue-49` (base `main` = `4bc0d13`), run
  from an empty `.cache` and no `.venv`, on linux-x86_64 with `uv`. No
  host-wide tool was installed or changed.
- Command: `bash scripts/setup-env.sh` (wall clock about 4 min 52 s).

## Outcome: pass (exit 0)

| check | result |
|---|---|
| klayout-tools fetch scripts @ `c572046be644`, sha256-checked (4 scripts) | ok |
| pins vs. fetch scripts cross-check (PDK commit and tarball sha256, sibling sha256, OpenVAF tag and sha256) | ok, no `sim/pdk.json` / `sim/toolchain.json` change needed |
| CMOS5L OSDI (six models) | built, all `OSDI ok` |
| `klt` | `pip`-installed `klayout-tools==0.8.0` into the in-checkout venv; ends `setup-env: klt: klt 0.8.0` |
| `klt drc --help`, `klt lvs --help` | succeed |
| second run | no-op for klt (no reinstall), ends `klt: klt 0.8.0` |

## Not exercised

- A venv holding the old dev build being replaced: the version check
  (`klt --version` must equal `klt <version_reported>`) is what triggers the
  reinstall (`uv venv --clear`), but this run started from no venv.
- A tampered fetch script aborting on sha256 mismatch: unchanged
  `fetch_verified` logic, not re-tested here.
- `klt signoff ... --check`: no committed signoff record exists on `main`.
