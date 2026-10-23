# Clean-clone `scripts/setup-env.sh` run, 2026-10-18

Append-only evidence for issue #4, item 1 (the Startable Subset). Environment
bring-up facts only; the one simulation quoted is a **simulated** `tt` probe
re-run, not a measurement.

## Setup

- Fresh `git clone` of `2AMLogic/sg13cmos5l-stdcells` into an empty scratch
  directory under `/tmp`, at `main` = `c2918e9c5f537012d4ee9df4927cc33fd971fc60`.
- Host: linux-x86_64 (Ubuntu), apt `ngspice-42` on PATH (below the floor of 44),
  no `openvaf` on PATH, `uv 0.12.23`. No host-wide tool was installed or changed.
- Command: `SETUP_JOBS=2 bash scripts/setup-env.sh`, no manual PDK step.
- Wall clock: 2026-10-18T00:01:09Z to 00:05:57Z (about 4 min 48 s, including the
  ngspice-47 build at `make -j2` and both PDK downloads).

## Outcome: pass (exit 0)

| step | result |
|---|---|
| klayout-tools fetch scripts @ `dce956c3c399`, sha256-checked | ok |
| pins vs. fetch scripts cross-check | ok |
| `ihp-sg13g2` sibling (IHP-Open-PDK v0.3.0), checksum verified | ok |
| `ihp-sg13cmos5l` @ `f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`, checksum verified | ok, with the expected warning below |
| ngspice | apt 42 below floor; pinned `ngspice-47` built inside the checkout |
| OpenVAF | `openvaf-r osdi_0.4-153-g2e066436` fetched and sha256-checked into the checkout (obtainable without touching the host) |
| SG13G2 sibling OSDI (psp103, psp103_nqs, r3_cmc, mosvar) | built, load-checked |
| CMOS5L OSDI (psp103, psp103_nqs, r3_cmc, mosvar, cap_cmomi, cap_cmomf) | built, all six `OSDI ok` |
| `klt` | `0.7.1.dev1755+gdce956c3c399`, venv inside the checkout; `drc`, `lvs` present |

Failures: none. One warning, verbatim from the PDK fetch script, already
documented in `sim/pdk.json` (`sibling.known_incomplete`):

```
WARNING: 262 dangling symlink(s) under .../ihp-sg13cmos5l
  ihp-sg13g2 sibling version: unknown (pinned subtree expects a matching dev commit;
  release v0.3.0 is known-incomplete -- see this script's header and pdks/README.md)
```

## Runnable-state check

After `source .cache/env.sh`, the committed single-corner request
`inverter_dc.tt-probe.request.json` was re-run with `klt sim --backend local`
(one corner, local; no grid). Status `pass`, ngspice 47, PDK
`ihp-sg13cmos5l fetched:f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`:

| measurement (simulated) | clean-clone run | `inverter_dc.tt-probe.report.json` |
|---|---|---|
| `voh_v` | 1.2 V | 1.2 V |
| `vol_v` | 5.9158e-08 V | 5.9158e-08 V |
| `vtrip_v` | 0.605841 V | 0.605841 V |

## Observation

`klt` warned that a second install of `ihp-sg13cmos5l` exists under the host's
`~/share/pdk` search root and that resolution is first-match-wins. In this run
`PDK_ROOT` took precedence, so the pinned tree was read. Requests that must be
reproducible can pin `models.pdk_root`. Not a defect of this repo.

## Not covered

The five-corner record is still open and blocked by 2AMLogic/klayout-tools#2727
(`klt sim --backend batch` refuses `ihp-sg13cmos5l`). Nothing here runs a corner
grid locally.
