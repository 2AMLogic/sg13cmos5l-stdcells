#!/usr/bin/env python3
"""Check design/cells.json: exactly 40 distinct, well-formed combinational cells.

Usage: check_catalog.py [catalog.json] [--celllist PDK_CELLLIST]

With --celllist, every `pdk_counterpart` must also appear in the PDK's
sg13cmos5l_stdcell cell list. Exit 0 on success, 1 with messages on failure.
"""
import json
import re
import sys

EXPECTED = 40
NAME_RE = re.compile(r"^s5l_[a-z0-9]+_[0-9]+$")
PIN_RE = re.compile(r"^[A-Z][A-Z0-9]*(_N)?$")
FORBIDDEN = ("dff", "dfr", "dfb", "dlh", "dll", "lgcp", "fill", "decap", "tie", "antenna", "sighold")


def check(catalog, celllist=None):
    errs = []
    cells = catalog.get("cells")
    if not isinstance(cells, list):
        return ["`cells` must be a list"]
    if len(cells) != EXPECTED:
        errs.append(f"expected {EXPECTED} cells, found {len(cells)}")
    if catalog.get("count") != EXPECTED:
        errs.append(f"`count` must be {EXPECTED}")
    seen, seen_pdk = set(), set()
    for i, c in enumerate(cells):
        if not isinstance(c, dict):
            errs.append(f"cells[{i}]: not an object")
            continue
        n = c.get("name", f"<cells[{i}]>")
        for key in ("name", "pdk_counterpart", "family", "drive", "inputs", "outputs"):
            if key not in c:
                errs.append(f"{n}: missing `{key}`")
        if not isinstance(c.get("name"), str) or not NAME_RE.match(c["name"]):
            errs.append(f"{n}: malformed name")
            continue
        if n in seen:
            errs.append(f"{n}: duplicate name")
        seen.add(n)
        if any(f in n for f in FORBIDDEN):
            errs.append(f"{n}: sequential/fill/decap/tie cells are not counted")
        if not isinstance(c.get("drive"), int) or c["drive"] < 1:
            errs.append(f"{n}: drive must be a positive integer")
        if n != f"s5l_{c.get('family')}_{c.get('drive')}":
            errs.append(f"{n}: name does not match family/drive")
        ins, outs = c.get("inputs"), c.get("outputs")
        if not (isinstance(ins, list) and ins and all(isinstance(p, str) and PIN_RE.match(p) for p in ins)):
            errs.append(f"{n}: inputs must be a non-empty list of pin names")
            continue
        if len(set(ins)) != len(ins):
            errs.append(f"{n}: duplicate input pin")
        if not (isinstance(outs, dict) and outs):
            errs.append(f"{n}: outputs must be a non-empty {{pin: function}} map")
            continue
        for p, f in outs.items():
            if p in ins:
                errs.append(f"{n}: pin {p} is both input and output")
            if not isinstance(f, str) or not f:
                errs.append(f"{n}: output {p} has no function")
            else:
                used = set(re.findall(r"[A-Z][A-Z0-9_]*", f))
                if not used <= set(ins):
                    errs.append(f"{n}: function of {p} uses undeclared pins {sorted(used - set(ins))}")
        pdk = c.get("pdk_counterpart")
        if pdk is not None:
            if pdk in seen_pdk:
                errs.append(f"{n}: duplicate pdk_counterpart {pdk}")
            seen_pdk.add(pdk)
            if celllist is not None and pdk not in celllist:
                errs.append(f"{n}: pdk_counterpart {pdk} not in PDK cell list")
        elif not c.get("no_counterpart_reason"):
            errs.append(f"{n}: no pdk_counterpart and no `no_counterpart_reason`")
    return errs


def main(argv):
    args = argv[1:]
    celllist = None
    if "--celllist" in args:
        i = args.index("--celllist")
        celllist = set(open(args[i + 1]).read().split())
        del args[i : i + 2]
    path = args[0] if args else "design/cells.json"
    errs = check(json.load(open(path)), celllist)
    for e in errs:
        print(f"FAIL: {e}")
    if not errs:
        print(f"OK: {EXPECTED} distinct well-formed cells in {path}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
