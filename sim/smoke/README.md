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

## Status of the five-corner run: blocked on the fleet

The five-corner requests are committed but **have no result record**. On this
host `KLT_SIM_BACKEND=batch`, and the multi-corner grid must go to the Spot
batch fleet, not to hand-launched local ngspice. The submit was refused before
any job started:

```
klt sim --backend batch inverter_dc.request.json
error: unsupported PDK 'ihp-sg13cmos5l' for the batch backend
(supported: sky130A, gf180mcu, sg13g2). ... a variant whose family has no
published AMI is unsupported even when it resolves locally.
```

Without `--backend`, `klt sim` falls back to `local` by itself for an OSDI
request, so the same request would have run all five corners on this host; that
was not done, by the host rule. The only local run is the single-corner debug
probe below. Closing this needs a fleet image that carries `ihp-sg13cmos5l`
(or a documented way to run a staged-PDK request on an existing image); it is
a change to the fleet spec, not to this repo (tracked as
[klayout-tools#2727](https://github.com/2AMLogic/klayout-tools/issues/2727)). Re-run when it exists:

```
source .cache/env.sh
klt sim inverter_dc.request.json   -o <out> --report-out records/inverter_dc.report.json
klt sim inverter_tran.request.json -o <out> --report-out records/inverter_tran.report.json
```
