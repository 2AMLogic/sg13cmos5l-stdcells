# Five-corner DC batch record, 2026-11-12 (issue #4)

Completes the DC half of the five-corner record; the transient half is in
[`five-corner.2026-11-11.md`](five-corner.2026-11-11.md). All values are
**simulated**, never measured.

## Job

| item | value |
|---|---|
| request | `sim/smoke/inverter_dc.request.json` (`tt/ff/ss/fs/sf`, 27 C, 1.2 V) |
| command | `klt sim inverter_dc.request.json --backend batch --wait-for-capacity 600` (client `klayout-tools==0.9.1` via `uvx`) |
| job id (`environment.remote.job_id`) | `klt-sim-fc0dbe6a24be` (aws-batch-fleet, spot `m6i.4xlarge`, exit 0, 10 s on the instance) |
| result | pass, 5/5 corners; report `inverter_dc.report.json` |
| klt | client 0.9.1 (`4d0d29be4fd991f499d59e783a908082d5e24c56`), fleet runner 0.9.0, `runner_compatibility: match` |
| PDK | IHP-Open-PDK `dev` `f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`, `ihp-sg13cmos5l` (`fetched:f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`), `pdk_stamp_comparison: match`, `models_staged: true` |
| ngspice | 46 (fleet runner) |

The earlier two submits (`klt-sim-4f437434e95a` and one uncaptured id) never
started. This submit launched about 25 s after submission and finished about
30 s later. The earlier non-start is still undiagnosed. The grid was never run
locally.

## DC transfer, `tt/ff/ss/fs/sf` at 27 C, 1.2 V (simulated)

| corner | `voh_v` (V) | `vol_v` (V) | `vtrip_v` (V) |
|---|---|---|---|
| tt | 1.2 | 6.03211e-08 | 0.605841 |
| ff | 1.2 | 4.98564e-07 | 0.606608 |
| ss | 1.2 | 7.16169e-09 | 0.602034 |
| fs | 1.2 | 3.27129e-08 | 0.571917 |
| sf | 1.2 | 1.67251e-07 | 0.638433 |

Hygiene edit: `environment.ngspice_binary` set to `null` in the committed report
(absolute runner path), as for the transient report.
