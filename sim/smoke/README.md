# sim/smoke -- ngspice smoke simulation (issue #4)

A toolchain smoke test, not a characterization: the PDK reference inverter
(`sg13cmos5l_inv_1` sizing, N 0.74 µm / 0.13 µm and P 1.12 µm / 0.13 µm) built
from the PDK's core LV devices `sg13_lv_nmos` / `sg13_lv_pmos`, at the 1.2 V
nominal of the PDK's own standard-cell library, into a fixed 10 fF load. Every
number here is **simulated**, never measured.

| file | what |
|---|---|
| `inverter_dc.cir`, `inverter_tran.cir` | circuit bodies (`klt sim` owns `.lib` / `.control`) |
| `inverter_dc.request.json` | DC transfer, `tt/ff/ss/fs/sf`, 27 C: `voh_v`, `vol_v`, `vtrip_v` |
| `inverter_tran.request.json` | transient, `tt/ff/ss/fs/sf`, 27 C: `tphl_s`, `tplh_s` |
| `records/` | evidence; see [`records/README.md`](records/README.md) |

Models come from `models.pdk: ihp-sg13cmos5l`, `libs.tech/ngspice/models/cornerMOSlv.lib`
sections `mos_tt mos_ff mos_ss mos_fs mos_sf`; the PSP103 OSDI is preloaded
from `$PDK_ROOT`. Both requests set `options.stage_model_inputs: true`, which
is what the batch backend needs to accept an OSDI preload.

## Status of the five-corner run

klt 0.9.1 (pinned in `layout/toolchain.json`) accepts `ihp-sg13cmos5l` on the
batch backend (klayout-tools#2727, fixed by #4733).

- `inverter_tran.request.json`: five corners passed on the fleet; record in
  [`records/five-corner.2026-11-11.md`](records/five-corner.2026-11-11.md).
- `inverter_dc.request.json`: five corners passed on the fleet (job
  `klt-sim-fc0dbe6a24be`); record in
  [`records/five-corner-dc.2026-11-12.md`](records/five-corner-dc.2026-11-12.md).
  The two earlier submits never started (undiagnosed).

To reproduce on the fleet (never hand-loop `ngspice -b` locally):

```
source .cache/env.sh
klt sim inverter_dc.request.json   --backend batch --wait-for-capacity 600 -o <out> --report-out records/inverter_dc.report.json
klt sim inverter_tran.request.json --backend batch --wait-for-capacity 600 -o <out> --report-out records/inverter_tran.report.json
```
