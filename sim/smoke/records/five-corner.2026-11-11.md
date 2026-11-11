# Five-corner batch record, 2026-11-11 (issue #4, partial)

All values are **simulated**, never measured.

## Pins and versions

| item | value (from `inverter_tran.report.json`) |
|---|---|
| klt | `klayout-tools==0.9.1`, commit `4d0d29be4fd991f499d59e783a908082d5e24c56` (client); fleet runner reports `0.9.0`, `runner_compatibility: match` |
| PDK | IHP-Open-PDK `dev` `f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`, `ihp-sg13cmos5l`, sibling `ihp-sg13g2` `fetched:0.3.0` |
| ngspice | 46 (fleet runner, `environment.engine_build`) |
| models | `cornerMOSlv.lib` sections `mos_tt mos_ff mos_ss mos_fs mos_sf`, staged to the runner (`models_staged: true`, `pdk_stamp_comparison: match`) |

The pin moved from klt 0.8.0 to 0.9.1 in `layout/toolchain.json`; 0.9.1 carries
klayout-tools#4733, which lets `klt sim --backend batch` accept `ihp-sg13cmos5l`.
`scripts/setup-env.sh` ran clean at the new pin (klt 0.9.1, all six OSDI models built).

## Jobs (all `klt sim --backend batch --wait-for-capacity 600`)

| job | request | result |
|---|---|---|
| `klt-sim-f8cf951c2ce6` | `inverter_dc.tt-probe.request.json` (single-corner probe, run first) | pass; `inverter_dc.tt-batch-probe.report.json` |
| `klt-sim-1d48736cc46b` | `inverter_tran.request.json` (5 corners) | pass 5/5; `inverter_tran.report.json` |
| `klt-sim-4f437434e95a` | `inverter_dc.request.json` (5 corners) | **never started**: `job.json` but no `status.json` after 123 s, no instance booted |
| (id not captured) | `inverter_dc.request.json`, earlier submit | no result within the 290 s client timeout I set; same symptom |

## Transient, `tt/ff/ss/fs/sf` at 27 C, 1.2 V, 10 fF (simulated)

| corner | `tphl_s` | `tplh_s` |
|---|---|---|
| tt | 5.71891e-11 | 6.27877e-11 |
| ff | 5.03208e-11 | 5.33131e-11 |
| ss | 6.6132e-11 | 7.34783e-11 |
| fs | 5.36524e-11 | 6.77037e-11 |
| sf | 6.12842e-11 | 5.78711e-11 |

## Not done

The five-corner **DC** record (`inverter_dc.report.json`) does not exist. Its two
batch submits were accepted but the fleet never launched them. Per the host rules
the grid was not run locally. The fleet has no cancel, so both jobs may still be
queued.

Hygiene edit: `environment.ngspice_binary` set to `null` in the committed reports
(absolute runner path); `engine_build.binary_sha256` carries the identity.
