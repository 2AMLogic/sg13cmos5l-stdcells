# sim/records

Append-only evidence for issue #44 (PDK-model check of the 40 generated
netlists). Everything here is **simulated**, never measured. Corner `tt`,
27 C, 1.2 V, one local `ngspice -b` per bench (ngspice 47, PSP103 OSDI), no
grid. PDK: IHP-Open-PDK `dev` commit `f7bca32694fe3d58be0cc7d9df4b9f5db7161a14`
(`ihp-sg13cmos5l`, sibling `ihp-sg13g2` `fetched:0.3.0`); model deck
`cornerMOSlv.lib` sha256 `03d50584...`, section `mos_tt`.

## Conclusion: `w` is the TOTAL width; `ng` splits it into fingers

No change to `design/gen_netlists.py` or `design/netlists/` is needed
(`gen_netlists.py --check`: 40 netlists fresh).

Source: the `sg13_lv_nmos` / `sg13_lv_pmos` wrapper in
`libs.tech/ngspice/models/sg13g2_moslv_mod.lib` (the `ihp-sg13g2` sibling tree,
which `ihp-sg13cmos5l` links to), `.subckt sg13_lv_nmos` from line 66. Its
geometry cards use `max(w/ng, wmin)` as the per-finger width for `as`/`ad`/
`ps`/`pd`, so the instance parameter `w` is the total and `w/ng` the finger.

Simulation (`sim/wng/wng_probe.*`, report `wng_probe.tt.report.json`), drain
current at Vgs = Vds = 1.2 V (PMOS: mirrored):

| device | w | ng | Id |
|---|---|---|---|
| NMOS A | 2 um | 1 | 847.2 uA |
| NMOS B | 2 um | 4 | 765.5 uA |
| NMOS D | 0.5 um | 1 | 191.4 uA |
| PMOS E | 2 um | 1 | 417.6 uA |
| PMOS F | 2 um | 4 | 424.3 uA |

At equal `w`, `ng=4` gives about the same current as `ng=1` (0.90x NMOS,
1.02x PMOS), not 4x, so `w` is not per-finger. The residual is the
finger/diffusion-geometry effect on `as`/`ad`. Id scales with `w` (D is 0.23x
A for 0.25x width).

## Truth tables on the real models

`pdk_truth_tables.tt.json`: all 40 cells, exhaustive input vectors (356
vector x output checks), real PDK models, no unresolved subckt/model errors;
0 failures at a 0.1 V tolerance. ngspice prints "Unknown model type
pspnqs103va - ignored" for the PDK's RF model variants; these are not
instantiated (`rfmode=0`) and do not affect the results.

Produced by `design/tests/test_pdk_models.py` at commit `7a38b2e`, since
retired (issue #108) as the second of two drivers for the same question. It
has no reproduce command at `main`; the script is recoverable with
`git show 7a38b2e:design/tests/test_pdk_models.py`. This record itself is
unchanged append-only evidence.

The current real-model truth-table check is `verification/functional/` (issue
#82): the same 40 cells and 356 vector x output checks, run as one
single-corner `klt sim` request with a `klt` report
(`verification/functional/records/tt.report.json`) and a negative control.
That is the record the manifest cites (`manifests/sg13cmos5l-stdcells.json`,
item 5), and it is what to run to re-derive this result today.
