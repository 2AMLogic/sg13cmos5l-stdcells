# sim/smoke/records

Append-only evidence for the toolchain smoke simulation. All values are
**simulated**.

## Single-corner `tt` debug probe (local)

One `ngspice -b` per bench, run with `klt sim --backend local` on the
`tt` corner only, to establish that the pinned PDK, the OSDI models and the
bench work end to end. This is a probe, not the five-corner record the issue
asks for (see [`../README.md`](../README.md#status-of-the-five-corner-run-blocked-on-the-fleet)).

| bench | corner | result (simulated) |
|---|---|---|
| `inverter_dc` | `tt/27C`, 1.2 V | `voh_v` = 1.2 V, `vol_v` = 5.9158e-08 V, `vtrip_v` = 0.605841 V |
| `inverter_tran` | `tt/27C`, 1.2 V, 10 fF | `tphl_s` = 5.71891e-11 s, `tplh_s` = 6.27877e-11 s |

Files: `inverter_{dc,tran}.tt-probe.request.json` (the requests that were run;
netlists are `../inverter_{dc,tran}.cir`) and `inverter_{dc,tran}.tt-probe.report.json`
(the `klt sim` envelopes).

Provenance, from the envelopes:

- PDK: IHP-Open-PDK `dev` commit `f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`,
  `ihp-sg13cmos5l`, with the `ihp-sg13g2` sibling at `fetched:0.3.0`
  (`provenance.pdk`). `models.lib` (`cornerMOSlv.lib`, sha256 `03d50584...`) is a
  relative symlink in the CMOS5L tree into the sibling `ihp-sg13g2`, so the
  LV MOS corner model used here is the sibling's file.
- ngspice 47 (built from the pinned tarball, sha256 `1dd3bc31...` for the
  binary, `environment.engine_build`), OSDI from openvaf-r `osdi_0.4-153-g2e066436`
  (`psp103.osdi` sha256 `85cec356...`).
- klt `0.7.1.dev1755+gdce956c3c399`, klayout 0.30.12.

Hygiene edit: `environment.ngspice_binary` was set to `null` in both reports
because it held an absolute host path; the binary's identity is its
`engine_build.binary_sha256`. Nothing else in the envelopes was changed.

The five-corner record (`inverter_dc.report.json`, `inverter_tran.report.json`)
does not exist yet.

## Clean-clone bring-up

[`setup-env.clean-clone.2026-10-18.md`](setup-env.clean-clone.2026-10-18.md)
records `scripts/setup-env.sh` run end to end from a fresh clone (pass, no manual
PDK step).
