# `scripts/setup-env.sh` at the klt 0.9.2 pin, 2026-11-15

Append-only evidence for issue #109. Environment bring-up facts only; no
simulation or measurement is claimed.

## Setup

- Worktree checkout of branch `feature/issue-109` (base `main` = `77511ed`),
  on linux-x86_64 with `uv`. No host-wide tool was installed or changed.
- The run started from a worktree whose gitignored `.cache/`, `.venv/` and
  `pdks/` were already provisioned (PDK at the pinned commit `f7bca326`,
  OSDI models built, ngspice taken from PATH), so this is the idempotent
  re-run path, not a from-empty bring-up: the old-venv-replaced and
  cold-download paths were not exercised here. The 0.8.0 record
  ([`setup-env.klt-0.8.0.2026-10-27.md`](setup-env.klt-0.8.0.2026-10-27.md))
  covers the from-empty path.
- Command: `bash scripts/setup-env.sh` (wall clock 3.7 s).

## Outcome: pass (exit 0)

| check | result |
|---|---|
| klayout-tools fetch scripts @ `046ba74652fc`, sha256-checked (4 scripts) | ok, all four re-hashes byte-identical to the 0.9.1 values |
| pins vs. fetch scripts cross-check (PDK commit and tarball sha256, sibling sha256, OpenVAF tag and sha256) | ok, no `sim/pdk.json` / `sim/toolchain.json` change needed |
| PDK `ihp-sg13cmos5l` | already present at the pinned commit `f7bca32694fe` |
| CMOS5L OSDI (six models) | all present, all six `OSDI ok` under PATH ngspice-47 |
| `klt` | venv already at the pin: `klayout-tools==0.9.2`, no reinstall needed; ends `setup-env: klt: klt 0.9.2` |
| `klt drc --help`, `klt lvs --help` | succeed (`klt_required_commands` check in-script) |
| `cocotb` | `2.1.0` at the `rtl/toolchain.json` pin |

## At-the-pin verification done beside this run (issue #109 ACs)

- `uvx --from "klayout-tools==0.9.2" klt characterize --help` lists
  `--resume`, `--split-grid`, `--wait-for-capacity` — the flags the recorded
  characterization runs used and 0.9.1 lacked.
- `klt drc --deck sg13cmos5l --top sg13cmos5l_inv_1` on
  `layout/smoke/sg13cmos5l_inv_1.gds` at 0.9.2: exit 0, `status: clean`,
  0 violations, deck `released: True` — same verdict as the recorded 0.7.1.dev
  evidence in `layout/smoke/README.md`.
- `klt lvs lvs_request.json` on the same cell at 0.9.2: exit 0,
  `status: match`. The recorded evidence is `mismatch` — filed as
  klayout-tools#3831 from that build — so the curated `sg13cmos5l` LVS now
  matches the PDK's reference inverter at this pin. `layout/smoke/`'s
  committed envelope is not regenerated (append-only evidence of its own
  build); a fresh committed record at 0.9.2 is future work, not part of #109.

## Not exercised

- A from-empty `.cache`/`.venv`/`pdks` bring-up at 0.9.2 (see Setup).
- A venv holding the old pin being replaced: this run started with the venv
  already at 0.9.2, so `uv venv --clear` + reinstall was not triggered.
- A tampered fetch script aborting on sha256 mismatch: unchanged
  `fetch_verified` logic, not re-tested here.
