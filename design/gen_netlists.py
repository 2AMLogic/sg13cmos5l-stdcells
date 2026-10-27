#!/usr/bin/env python3
"""Generate transistor-level SPICE netlists for the 40-cell catalog.

Usage: gen_netlists.py [--check] [--catalog design/cells.json] [--out design/netlists]

Default mode (re)writes one `<cell>.spice` per catalog cell under --out.
`--check` regenerates in memory and exits 1 on any difference against the
files on disk (changed, missing, or stray `.spice` files); this is the
declared freshness check for `klt signoff --attest 1`. Output is
deterministic (sorted, no timestamps), so the check is a byte compare.

Topology (PDK-independent). Each output function is parsed into an AST
(`!` `*` `^` `+`, `!` binds tightest, then `*`, `^`, `+`) and put in negation
normal form over literals; XOR is expanded to (a*!b)+(!a*b). A literal that
appears inverted gets one shared unit inverter per cell. The remaining
function g is positive in its literals, so static CMOS applies directly:
pull-down = g (AND series, OR parallel), pull-up = the dual, stage output = !g.
  * output is `!g`            -> one inverting stage drives the pin;
  * output is `g` (non-inv.)  -> an inverting stage then an output inverter.

Sizing rule (SG13CMOS5L configuration; the only PDK-specific part):
  * unit widths are the sg13cmos5l_inv_1 reference: N 740 nm, P 1120 nm,
    L 130 nm, on `sg13_lv_nmos` / `sg13_lv_pmos`, supply 1.20 V;
  * a device's width is unit * stage_scale * D, where D is the longest series
    path through that device in its own pull network (stack compensation);
  * stage_scale is the drive for the stage that drives the pin; for the first
    stage of a non-inverting cell it is max(1, drive // 2); input inverters
    for inverted literals are unit size;
  * row fit: the width `w` is the TOTAL device width, split into `ng` equal
    fingers, each at most FINGER_MAX_N / FINGER_MAX_P. These caps keep the N
    and P diffusion rows (1000 + 1200 nm) plus rail clearance inside the
    3.36 um row target (rail 0.44 um at the cell boundary, 0.7 um reserved for
    the N-P diffusion spacing). This is a sizing constraint, not a layout
    claim: the row height is a target (spec/target-spec.md), fallback 3.78 um.
"""
import argparse
import difflib
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent

VDD_V = 1.20
L_NM = 130
UNIT_N_NM = 740
UNIT_P_NM = 1120
FINGER_MAX_N = 1000
FINGER_MAX_P = 1200
ROW_UM = 3.36
RAIL_UM = 0.44
DIFF_RESERVE_UM = 0.70
assert (FINGER_MAX_N + FINGER_MAX_P) / 1000 <= ROW_UM - RAIL_UM - DIFF_RESERVE_UM

TOKEN_RE = re.compile(r"\s*(?:([A-Z][A-Z0-9_]*)|(.))")


# ---------------------------------------------------------------- parsing
def parse(expr):
    toks = []
    for m in TOKEN_RE.finditer(expr):
        if m.group(1):
            toks.append(("id", m.group(1)))
        elif m.group(2) and m.group(2).strip():
            toks.append((m.group(2), m.group(2)))
    pos = [0]

    def peek():
        return toks[pos[0]][0] if pos[0] < len(toks) else None

    def take(kind):
        if peek() != kind:
            raise ValueError(f"expected {kind!r} in {expr!r}")
        pos[0] += 1
        return toks[pos[0] - 1][1]

    def nary(op, sub, sym):
        items = [sub()]
        while peek() == sym:
            take(sym)
            items.append(sub())
        return items[0] if len(items) == 1 else (op, items)

    def atom():
        if peek() == "!":
            take("!")
            return ("not", atom())
        if peek() == "(":
            take("(")
            e = or_()
            take(")")
            return e
        return ("var", take("id"))

    def and_():
        return nary("and", atom, "*")

    def xor_():
        items = [and_()]
        while peek() == "^":
            take("^")
            items.append(and_())
        e = items[0]
        for r in items[1:]:
            e = ("xor", e, r)
        return e

    def or_():
        return nary("or", xor_, "+")

    e = or_()
    if pos[0] != len(toks):
        raise ValueError(f"trailing input in {expr!r}")
    return e


def evaluate(e, env):
    k = e[0]
    if k == "var":
        return env[e[1]]
    if k == "not":
        return 1 - evaluate(e[1], env)
    if k == "and":
        return int(all(evaluate(x, env) for x in e[1]))
    if k == "or":
        return int(any(evaluate(x, env) for x in e[1]))
    return evaluate(e[1], env) ^ evaluate(e[2], env)


def nnf(e, neg=False):
    """Negation normal form: ('lit', name, inverted) / ('and'|'or', [..])."""
    k = e[0]
    if k == "var":
        return ("lit", e[1], neg)
    if k == "not":
        return nnf(e[1], not neg)
    if k == "xor":
        a, b = e[1], e[2]
        return nnf(("or", [("and", [a, ("not", b)]), ("and", [("not", a), b])]), neg)
    op = k if not neg else ("or" if k == "and" else "and")
    kids = [nnf(x, neg) for x in e[1]]
    flat = []
    for kid in kids:
        flat.extend(kid[1] if kid[0] == op else [kid])
    return flat[0] if len(flat) == 1 else (op, flat)


def split_output_inversion(e):
    neg = False
    while e[0] == "not":
        neg, e = not neg, e[1]
    return neg, e


# ---------------------------------------------------------------- networks
def depth(t):
    if t[0] == "lit":
        return 1
    ds = [depth(x) for x in t[1]]
    return sum(ds) if t[0] == "and" else max(ds)


class Cell:
    def __init__(self, name):
        self.name = name
        self.devices = []  # (kind, drain, gate, source, w_nm, ng)
        self.counter = 0

    def node(self, hint="n"):
        self.counter += 1
        return f"{hint}{self.counter}"

    def add(self, kind, d, g, s, w_nm):
        cap = FINGER_MAX_N if kind == "n" else FINGER_MAX_P
        ng = 1
        while w_nm % (10 * ng) or w_nm // ng > cap:
            ng += 1
        self.devices.append((kind, d, g, s, w_nm, ng))

    def network(self, tree, kind, top, bot, signal, unit, scale, outside=0):
        """Emit tree between top and bot. `kind` n: AND=series; p: AND=parallel."""
        if tree[0] == "lit":
            self.add(kind, top, signal(tree), bot, unit * scale * (outside + 1))
            return
        series = (tree[0] == "and") == (kind == "n")
        kids = tree[1]
        if not series:
            for k in kids:
                self.network(k, kind, top, bot, signal, unit, scale, outside)
            return
        ds = [depth_for(k, kind) for k in kids]
        nodes = [top] + [self.node() for _ in kids[:-1]] + [bot]
        for i, k in enumerate(kids):
            others = sum(ds) - ds[i]
            self.network(k, kind, nodes[i], nodes[i + 1], signal, unit, scale, outside + others)

    def stage(self, g, out, signal, scale):
        self.network(g, "n", out, "VSS", signal, UNIT_N_NM, scale)
        self.network(g, "p", out, "VDD", signal, UNIT_P_NM, scale)

    def inverter(self, a, y, scale):
        self.add("n", y, a, "VSS", UNIT_N_NM * scale)
        self.add("p", y, a, "VDD", UNIT_P_NM * scale)


def depth_for(t, kind):
    """Series depth of a subtree in the n (AND series) or p (OR series) network."""
    if t[0] == "lit":
        return 1
    ds = [depth_for(x, kind) for x in t[1]]
    series = (t[0] == "and") == (kind == "n")
    return sum(ds) if series else max(ds)


def build(cell):
    c = Cell(cell["name"])
    drive = cell["drive"]
    inverted = {}  # input pin -> inverted-literal node (shared per cell)

    def signal(lit):
        _, name, inv = lit
        if not inv:
            return name
        if name not in inverted:
            inverted[name] = f"{name}_b"
            c.inverter(name, inverted[name], 1)
        return inverted[name]

    for pin, fn in sorted(cell["outputs"].items()):
        out_neg, inner = split_output_inversion(parse(fn))
        g = nnf(inner)
        if out_neg:
            c.stage(g, pin, signal, drive)
        else:
            mid = f"{pin}_i"
            c.stage(g, mid, signal, max(1, drive // 2))
            c.inverter(mid, pin, drive)
    return c


# ---------------------------------------------------------------- emission
def fmt_w(nm):
    return f"{nm}n"


def render(cell):
    c = build(cell)
    ins = cell["inputs"]
    outs = sorted(cell["outputs"])
    out = [
        f"* {cell['name']} -- generated by design/gen_netlists.py from design/cells.json; do not edit.",
        f"* family {cell['family']}, drive {cell['drive']}, sg13_lv devices, L={L_NM}n, supply {VDD_V:.2f} V.",
    ]
    for p in outs:
        out.append(f"* {p} = {cell['outputs'][p]}")
    out.append(f".subckt {cell['name']} {' '.join(ins + outs)} VDD VSS")
    nn = pp = 0
    for kind, d, g, s, w, ng in c.devices:
        if kind == "n":
            tag, model, bulk, nn = f"XMN{nn}", "sg13_lv_nmos", "VSS", nn + 1
        else:
            tag, model, bulk, pp = f"XMP{pp}", "sg13_lv_pmos", "VDD", pp + 1
        out.append(f"{tag} {d} {g} {s} {bulk} {model} w={fmt_w(w)} l={L_NM}n ng={ng} m=1")
    out.append(f".ends {cell['name']}")
    return "\n".join(out) + "\n"


def generate(catalog):
    return {f"{c['name']}.spice": render(c) for c in catalog["cells"]}


def check(files, outdir):
    errs = []
    on_disk = {p.name for p in outdir.glob("*.spice")} if outdir.is_dir() else set()
    for name, text in sorted(files.items()):
        path = outdir / name
        if name not in on_disk:
            errs.append(f"missing: {path}")
        elif path.read_text() != text:
            diff = difflib.unified_diff(
                path.read_text().splitlines(), text.splitlines(), f"{name} (committed)", f"{name} (regenerated)", lineterm="", n=0
            )
            errs.append(f"stale: {path}\n" + "\n".join(diff))
    for name in sorted(on_disk - set(files)):
        errs.append(f"stray: {outdir / name} is not in the catalog")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true", help="fail if committed netlists differ from regenerated ones")
    ap.add_argument("--catalog", default=str(HERE / "cells.json"))
    ap.add_argument("--out", default=str(HERE / "netlists"))
    a = ap.parse_args(argv)
    files = generate(json.load(open(a.catalog)))
    outdir = pathlib.Path(a.out)
    if a.check:
        errs = check(files, outdir)
        for e in errs:
            print(e, file=sys.stderr)
        if errs:
            print(f"gen_netlists: {len(errs)} netlist(s) out of date; run design/gen_netlists.py", file=sys.stderr)
            return 1
        print(f"gen_netlists: {len(files)} netlists fresh")
        return 0
    outdir.mkdir(parents=True, exist_ok=True)
    for stale in outdir.glob("*.spice"):
        if stale.name not in files:
            stale.unlink()
    for name, text in files.items():
        (outdir / name).write_text(text)
    print(f"gen_netlists: wrote {len(files)} netlists to {outdir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
