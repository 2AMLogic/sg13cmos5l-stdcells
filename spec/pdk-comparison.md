# PDK comparison: SG13CMOS5L vs SG13G2

Input to [`target-spec.md`](target-spec.md) and
[decision record 0001](decision-records/0001-ratify-target-spec.md).

Every row cites the PDK file or document it was read from. A row not read from
a document is labelled **not verified**. `$PDK` is the installed
`ihp-sg13cmos5l` tree and `$PDK_G2` the installed `ihp-sg13g2` tree (the paths
are install-local and deliberately not recorded). The installed SG13CMOS5L tree
carries no version stamp (`klt pdk list` reports none), so the revision read is
identified by the documents' own revision fields:

| Source | Revision read |
|---|---|
| `$PDK/libs.doc/doc/SG13CMOS5L_os_layout_rules.pdf` | Rev. 0.1 (2025-12-08) |
| `$PDK/libs.doc/doc/SG13CMOS5L_os_process_spec.pdf` | Rev. 0.2 (2025-12-15) |
| `$PDK/libs.ref/sg13cmos5l_stdcell/doc/ReleaseNotes.txt` | Rev 0.1.4 (17 Feb 2026) |
| `$PDK_G2/libs.doc/doc/SG13G2_os_layout_rules.pdf` | Rev. 0.4 (2024-12-19) |

The formal PDK pin belongs to issue #4; until it lands, the revisions above are
the citation.

## What the two PDKs share

| Item | SG13CMOS5L | SG13G2 | Same? | Source / method |
|---|---|---|---|---|
| Core MOS flavor in the reference cells | `sg13_lv_nmos`, `sg13_lv_pmos` only (462 instances each) | same flavors | yes | `$PDK/libs.ref/sg13cmos5l_stdcell/spice/sg13cmos5l_stdcell.spice` |
| Gate length used by reference cells | 0.13 µm | 0.13 µm | yes | same netlist (`l=130.00n`) |
| LV MOS model cards | `sg13g2_moslv_parm.lib`, `cornerMOSlv.lib` byte-identical; `sg13g2_moslv_mod.lib` and `_stat.lib` differ in 2 lines each (`mm_ok` 0 vs 1 on a pre-layout binned instance) | | effectively | `diff` of `$PDK/libs.tech/ngspice/models/` against `$PDK_G2/…` |
| NMOS/PMOS process-control targets (VTN10x013 0.50 V, IDSN013 480 µA/µm, VTP10x013 −0.47 V, …) | identical | identical | yes | process spec §2.1 vs SG13G2 process spec |
| Metal1 rules (M1.a–M1.k: width 0.16, space 0.18, area 0.09, density 35–60 %) | identical | identical | yes | layout rules §5.14 |
| Metal2–4 rules (Mn.a–Mn.k: width 0.20, space 0.21, area 0.144) | identical | identical | yes | layout rules §5.15 |
| NWell, Activ, GatPoly, pSD, nSD:block, Cont, ContBar, Via1–3 rules | identical | identical | yes | rule-ID/value rows of layout rules §5.1–5.18 diffed after text extraction; the only differing rows are listed below |
| Digital-design boundary rules (DigiBnd: NW.c1/d1/e1/f1, Cnt.c) | present, same values | present | yes | layout rules §8.1 |
| Standard-cell layout views | LEF macros are identical to SG13G2's after renaming the prefix; same 84 macros | | yes | `diff` of `sg13cmos5l_stdcell.lef` vs `sg13g2_stdcell.lef` (0 differing lines after `sed` of the prefix) |
| Minimum row height the rules allow | **not verified** — neither rule document states one; it follows from the generator's layout, not from a rule | | — | see target-spec "Row height" |

## What differs

| Item | SG13CMOS5L | SG13G2 | Consequence for the cells | Source |
|---|---|---|---|---|
| Metal stack | Metal1–Metal4 (thin Al) + TopMetal1 (thick Al); no Metal5, no TopMetal2, no Via4, no TopVia2 | Metal1–Metal5 + TopMetal1 + TopMetal2 | One fewer signal routing layer (M2–M4 vs M2–M5); one fewer thick layer for power. Intra-cell routing (M1 only) is unaffected | process spec §1.1, §1.4; `sg13cmos5l_tech.lef` header ("Removed: Via4, Metal5, TopVia2, TopMetal2") |
| TopVia1 landing layer | Metal4 | Metal5 | rule TV1.c value unchanged (0.10) | layout rules TV1.c |
| TopMetal1 direction | horizontal | vertical | Power straps on TopMetal1 run parallel to the M1 rails | `sg13cmos5l_tech.lef` vs `sg13g2_tech.lef` |
| Routing pitch declared in tech LEF | all routing layers `PITCH 0.48 0.42` | M1/M3/M5 0.42, M2/M4 0.48 | Tech LEF no longer states per-layer pitch; the per-layer tracks are in `tracks.info` (below) | both tech LEFs |
| Track grid (`tracks.info`) | M1 0.42, M2 0.48, M3 0.42, M4 0.48, TM1 offset 1.64 pitch 2.28 | not read | M2/M4 tracks (0.48) do not align with a 0.42 pin grid; see target-spec "Pin access" | `$PDK/libs.tech/librelane/sg13cmos5l_stdcell/tracks.info` |
| TopMetal1 pitch | tech LEF `PITCH 3.28`; `tracks.info` 2.28; release notes say the tech-LEF value was changed 2.28 → 3.28 (#722) | tech LEF 3.28 | Internal PDK inconsistency; affects PDN, not cells. Recorded, not resolved here | tech LEF; `tracks.info`; `ReleaseNotes.txt` |
| Library supply options | 1.2 V family (1.08 / 1.20 / 1.32 V) **and** a 1.5 V family (1.35 / 1.50 / 1.65 V) | not compared | Origin has no 1.5 V row; see target-spec "Supply" | `$PDK/libs.ref/sg13cmos5l_stdcell/lib/*.lib` (`nom_voltage`) |
| `klt` deck | built-in `sg13cmos5l` deck, `released: False`, device classes nfet, pfet, cap_cmomi, cap_cmomf, resistor (no `dantenna`/`dpantenna`, which the `sg13g2` deck has) | built-in `sg13g2` deck, `released: False` | Antenna diode cell (`antennanp`) is not extractable by device class; actual DRC/LVS behavior **not verified** here (issue #4) | `klt deck info` (klt 0.7.1.dev1755+gdce956c3c399) |
| Rule-document wording | SG13G2-only rows: TM1Fil.d, NW.f1 revision note | | none for the cell set | diff described above |

## The baseline, `sg13cmos5l_stdcell`

Read from `$PDK/libs.ref/sg13cmos5l_stdcell/` and `$PDK/libs.tech/librelane/`.

| Item | Value | Source |
|---|---|---|
| Placement site `CoreSite` | 0.48 µm × **3.78 µm** (9 tracks of 0.42 µm) | `lef/sg13cmos5l_stdcell.lef`; `config.tcl` (`PLACE_SITE_WIDTH 0.48`, `PLACE_SITE_HEIGHT 3.78`) |
| Power rails | Metal1, 0.44 µm wide, centered on the cell boundary (`RECT 0 -0.22 … 0.22`); `FP_PDN_RAIL_WIDTH 0.44` | LEF `VSS`/`VDD` pins; `config.tcl` |
| Cell set | 84 macros (combinational, flip-flops, latches, scan flops, clock gates, tri-state buffers, delay gates, tie, antenna, fill, decap, `sighold`) | `doc/sg13cmos5l_stdcell.celllist` |
| Views shipped | CDL, GDS, LEF, Liberty, SPICE, Verilog (+ UDP) | directory listing |
| Liberty corners | typ 1.20 V/25 °C, fast 1.32 V/−40 °C, slow 1.08 V/125 °C; and typ 1.50 V/25 °C, fast 1.65 V/−40 °C, slow 1.35 V/125 °C | `lib/` |
| Liberty tables | delay/transition 7 × 7: input slew 0.0186 … 2.5074 ns, output load 0.001 … 0.3 pF (`TIMING_DELAY_7x7ds1`); constraint 4 × 4 | `lib/…typ_1p20V_25C.lib` templates |
| Reference flow | LibreLane config with STA corners nom_typ_1p20V_25C, nom_fast_1p32V_m40C, nom_slow_1p08V_125C; default corner typ 1.20 V | `libs.tech/librelane/config.tcl` |
| Provenance | the library was migrated from `sg13g2_stdcell` (rev 0.1.4 is its first `sg13cmos5l_stdcell` release) | `ReleaseNotes.txt` |

The baseline is therefore **geometrically the SG13G2 library** run on a
different stack. This repo's benchmark compares against it, not against
SG13G2 numbers.

## Generator fit

No cell generator exists upstream yet: `2AMLogic/sg13g2-stdcells` at
`f450813c6a5eecf3cf67aaf899db90d11f4ee68c` carries a harness, `flow/`, `views/`
and a placeholder `spec/` only (its issue #2 "Harness bootstrap" and #3 survey
are open). So no generator parameter can be shown to change and no generator
rule gap can be shown. **No upstream issue is filed** because there is nothing
to cite; the check is repeated when a generator is pinned (issue #3 / the
retarget issue). What can be said ahead of that: the rules that a generator
reads for the cell body (Activ, GatPoly, Cont, Metal1, NWell, pSD, nSD) are
identical, and the stack difference sits above Metal1.
