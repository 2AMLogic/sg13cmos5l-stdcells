#!/usr/bin/env python3
"""Single-point sizing probe for issue #129 (operator ruling 2026-11-18).

Question: can a resized `_1` stack cell clear the ratified grid-validity bound
(2.5074 ns) on its stacked-NMOS rise arcs at the failing point -- SS / 1.08 V /
125 C, ramp 4.179 ns rail-to-rail, load 0.3 pF (decision record 0005 section
2) -- so item 5 can reach `met` without touching the grid row?

This script derives, from the committed design/netlists (never edits them),
per-variant copies of the three failing cells (`s5l_nand3_1`, `s5l_nand3b_1`,
`s5l_nand4_1`) with generator-style width overrides, plus one testbench and one
single-corner `klt sim` request per variant. The testbench instantiates the
same ten arcs in the same hold states as verification/functional/tb_corners.cir
and measures the same 50%-to-50% delays under the same names, so the numbers
are directly comparable with verification/functional/records/corners.report.json.

Device selection, mirroring the generator's families:
  stack NMOS  = every `XMN*` line touching an internal node (n1/n2/n3) --
                for s5l_nand3b_1 this excludes the A_N inverter device;
  output PMOS = every `XMP*` line whose drain is `Y` -- for s5l_nand3b_1 this
                excludes the A_N inverter device.

Variants (all applied to all three cells; widths in the `w=` field, ng kept
unless said):
  v0_baseline      committed sizing (740n/finger NMOS stack, 1120n PMOS);
                   reproduces the recorded failing numbers and so validates
                   the probe against the record
  v1_pmos_2240     output PMOS ng 1 -> 2 (w 1120n -> 2240n, per finger 1120n)
  v2_nmos_560      stack NMOS per-finger 740n -> 560n (nand3/3b w=1680n ng=3,
                   nand4 w=2240n ng=4)
  v3_pmos_2240_nmos_560   v1 + v2 combined
  v4_pmos_1680     output PMOS ng 1 -> 2 at 840n/finger (w 1120n -> 1680n)

Everything is SIMULATED, never measured. The bound 2.5074e-9 s is quoted from
spec/decision-records/0005 (the ratified grid-validity bound); it is not
redefined here and `margin.py` is not touched. Run one variant:

    klt sim sim/characterize/probe_item5_sizing/gen/v0_baseline/probe.ss.request.json \
        --backend local --pdk-root "$PDK_ROOT" -o <scratch dir>
"""
from __future__ import annotations

import json
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent  # .../sim/characterize/probe_item5_sizing
REPO = HERE.parent.parent.parent                # repo root
NETLISTS = REPO / "design" / "netlists"

CELLS = ["s5l_nand3_1", "s5l_nand3b_1", "s5l_nand4_1"]
LIMIT_A = 2.5074e-9                        # ratified grid-validity bound (0005)

# tb_corners.cir stimulus, verbatim: unitless PWL, Bin scales it to the rail.
VSHAPE = "Vshape vshape 0 PWL(0 0 30.0n 0 34.179n 1 64.179n 1 68.358n 0 98.358n 0)"
ANALYSIS = "20p 98.358n 0 50p"

# arc -> (subckt port order for the instance line), from tb_corners.cir;
# the switching input is `vin`, every held input `vdd` or `0`.
ARCS = {
    "s5l_nand3_1": {
        "a": ["vin", "vdd", "vdd"],
        "b": ["vdd", "vin", "vdd"],
        "c": ["vdd", "vdd", "vin"],
    },
    "s5l_nand3b_1": {
        "a_n": ["vin", "vdd", "vdd"],
        "b": ["0", "vin", "vdd"],
        "c": ["0", "vdd", "vin"],
    },
    "s5l_nand4_1": {
        "a": ["vin", "vdd", "vdd", "vdd"],
        "b": ["vdd", "vin", "vdd", "vdd"],
        "c": ["vdd", "vdd", "vin", "vdd"],
        "d": ["vdd", "vdd", "vdd", "vin"],
    },
}

# Arcs whose switching input reaches the output non-invertingly (the A_N
# input of nand3b is double-inverted): the rising output edge follows the
# RISING input edge, so the TRIG pairing flips. All other arcs here are
# inverting (rising output follows the falling input edge), as
# corners.request.json's own spice lines encode it.
NON_INVERTING = {("s5l_nand3b_1", "a_n")}

VARIANTS = {
    "v0_baseline": {},
    "v1_pmos_2240": {"pmos_ng": 2},
    "v2_nmos_560": {"nmos_finger_nm": 560},
    "v3_pmos_2240_nmos_560": {"pmos_ng": 2, "nmos_finger_nm": 560},
    "v4_pmos_1680": {"pmos_ng": 2, "pmos_finger_nm": 840},
}


def _node(cell: str, arc: str) -> str:
    """The B-source node a (cell, arc) is measured on: the instance index in
    the fixed CELLS/ARCS iteration order, identical in testbench() and
    request() by construction."""
    idx = 0
    for c in CELLS:
        for a in ARCS[c]:
            if c == cell and a == arc:
                return f"n{idx}"
            idx += 1
    raise KeyError((cell, arc))

_NMOS_INTERNAL = re.compile(r"\bn\d+\b")
_W = re.compile(r"w=(\d+)n")
_NG = re.compile(r"ng=(\d+)")


def override_netlist(text: str, cell: str, spec: dict, variant: str) -> str:
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("XMP") or stripped.startswith("XMN"):
            parts = stripped.split()
            is_pmos = stripped.startswith("XMP")
            is_output_pmos = is_pmos and parts[1] == "Y"
            is_stack_nmos = (not is_pmos) and bool(_NMOS_INTERNAL.search(stripped))
            new = line
            if is_output_pmos and "pmos_ng" in spec:
                ng = int(_NG.search(new).group(1))
                w = int(_W.search(new).group(1))
                finger = spec.get("pmos_finger_nm", w // ng)
                new = _NG.sub(f"ng={spec['pmos_ng']}", new)
                new = _W.sub(f"w={finger * spec['pmos_ng']}n", new)
            if is_stack_nmos and "nmos_finger_nm" in spec:
                ng = int(_NG.search(new).group(1))
                new = _W.sub(f"w={spec['nmos_finger_nm'] * ng}n", new)
            if new != line:
                out.append(f"* {variant}: {stripped.split()[0]} resized\n" + new)
                continue
        out.append(line)
    header = (
        f"* issue #129 sizing probe, variant {variant}: derived from "
        f"design/netlists/{cell}.spice by sim/characterize/probe_item5_sizing/gen_probe.py.\n"
        f"* NOT a design netlist; probe evidence only. SIMULATED, never measured.\n"
    )
    return header + "\n".join(out) + "\n"


def testbench(variant_dir: pathlib.Path, variant: str) -> str:
    # The committed tb_corners.cir is circuit-only: klt sim injects the
    # .meas statements from the request's measurements[].spice fields.
    lines = [
        f"* issue #129 sizing probe, variant {variant}; generated by gen_probe.py.",
        "* Same arcs, hold states, stimulus, load and measurement names as",
        "* verification/functional/tb_corners.cir (decision record 0005's point:",
        "* slew 2.5074 ns 20-80% applied as a 4.179 ns rail-to-rail ramp, load 0.3 pF).",
        "* Single corner (SS / 1.08 V / 125 C) per request; run locally.",
        "* SIMULATED, never measured.",
        "Vdd vdd 0 1.2",
        "* Unitless 0 -> 1 -> 0 shape; Bin scales it to the corner's rail.",
        VSHAPE,
        "Bin vin 0 V = v(vdd)*v(vshape)",
    ]
    idx = 0
    for cell in CELLS:
        src = (NETLISTS / f"{cell}.spice").read_text()
        overridden = override_netlist(src, cell, VARIANTS[variant], variant)
        rel = variant_dir / f"{cell}.spice"
        rel.write_text(overridden)
        lines.append(f".include {rel}")
        ports = ARCS[cell]
        for arc, drive in ports.items():
            term = " ".join(drive)
            lines.append(f"* arc {cell} {arc.upper()} -> Y (probe variant {variant})")
            lines.append(f"X{idx} {term} a{idx} vdd 0 {cell}")
            lines.append(f"C{idx} a{idx} 0 0.3p")
            lines.append(f"B{idx} n{idx} 0 V = v(a{idx})/v(vdd)")
            idx += 1
    return "\n".join(lines) + "\n"


def request(variant_dir: pathlib.Path, corner: str = "ss") -> str:
    corners = {
        "ss": ({"name": "ss", "sections": ["mos_ss"]}, 125, 1.08),
        "tt": ({"name": "tt", "sections": ["mos_tt"]}, 25, 1.2),
        "ff": ({"name": "ff", "sections": ["mos_ff"]}, -40, 1.32),
    }
    process, temp, vdd = corners[corner]
    req = {
        "_comment": (
            f"issue #129 single-point sizing probe ({corner}): the ten arcs of "
            "s5l_nand3_1/s5l_nand3b_1/s5l_nand4_1 at decision record 0005's "
            f"grid point (ramp 4.179 ns rail-to-rail, load 0.3 pF), corner "
            f"{process['name']} / {vdd} V / {temp} C, against the ratified "
            "grid-validity bound. One corner per request => runs local. "
            "SIMULATED, never measured."
        ),
        "engine": "ngspice",
        "netlist": "tb_probe.cir",
        "models": {
            "pdk": "ihp-sg13cmos5l",
            "lib": "libs.tech/ngspice/models/cornerMOSlv.lib",
        },
        "corners": {
            "units": [
                {
                    "process": process,
                    "temperature_c": temp,
                    "supply_v": {"Vdd": vdd},
                }
            ]
        },
        "analysis": {"kind": "tran", "args": ANALYSIS},
        "options": {
            "osdi_preload": [
                "$PDK_ROOT/ihp-sg13cmos5l/libs.tech/ngspice/osdi/psp103.osdi",
                "$PDK_ROOT/ihp-sg13cmos5l/libs.tech/ngspice/osdi/psp103_nqs.osdi",
            ],
            "timeout_s": 300,
        },
        "measurements": [],
    }
    for cell in CELLS:
        for arc in ARCS[cell]:
            non_inv = (cell, arc) in NON_INVERTING
            for edge in ("r", "f"):
                trig = ("RISE" if non_inv else "FALL") if edge == "r" else (
                    "FALL" if non_inv else "RISE"
                )
                targ = "RISE" if edge == "r" else "FALL"
                req["measurements"].append(
                    {
                        "name": f"d_{cell}_y_{arc}_{edge}",
                        "unit": "s",
                        "limits": {"max": LIMIT_A},
                        "spec_row": "t_stage_delay_grid_bound",
                        "spice": (
                            f".meas tran d_{cell}_y_{arc}_{edge} TRIG v(vshape) "
                            f"VAL=0.5 {trig}=1 TARG v({_node(cell, arc)}) "
                            f"VAL=0.5 {targ}=1"
                        ),
                    }
                )
    return json.dumps(req, indent=2) + "\n"


def main() -> None:
    for variant in VARIANTS:
        vdir = HERE / "gen" / variant
        vdir.mkdir(parents=True, exist_ok=True)
        (vdir / "tb_probe.cir").write_text(testbench(vdir, variant))
        for corner in ("ss", "tt", "ff"):
            (vdir / f"probe.{corner}.request.json").write_text(request(vdir, corner))
        print(f"wrote {vdir}")


if __name__ == "__main__":
    main()
