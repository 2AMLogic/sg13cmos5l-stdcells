#!/usr/bin/env python3
"""Checks for the corner-matrix timing-arc evidence (issue #120).

The arc list decides what the corner sweep measures, so it is checked against
two things it must not be allowed to drift from:

  * the **RTL models** -- the arcs are derived by evaluating the boolean
    expressions in `design/cells.json`, and are only as good as that
    evaluation. Every cell's every vector is compared against the exhaustive
    truth tables `rtl/<cell>.v` prints through iverilog (the same oracle
    `compare.py` uses), so an expression this sweep reads differently from
    the shipped RTL fails here rather than silently mis-measuring the
    library. Since issue #125 both sides parse with the one shared parser
    (`design/gen_netlists.py`), so there is no second grammar left to
    disagree. What this still guards is the two independent *evaluators* of
    that one parse tree -- `gen_netlists.evaluate()`, which derives the arcs,
    against `gen_models.to_verilog()` as iverilog elaborates it.
  * the **characterized Liberty** -- the arc count must equal the number of
    `timing ()` groups in the recorded TT `.lib`, so an arc the
    characterization found but this sweep does not measure (or vice versa) is
    a failure.

Then, if `records/corners.report.json` exists, the recorded report is checked
for shape: every arc measured at every ratified corner, every measurement
limited and spec-row tagged. Whether those measurements *passed* is the
report's own verdict and is printed, not asserted -- a recorded failure is
evidence, not a broken test (spec/decision-records/0005).

The same two checks run over the all-state sweep (issue #124), which measures
every side-input state that propagates an arc rather than the first one:

  * the **enumeration** -- `arc_states()` must agree with `arcs()` about which
    arcs exist and about each arc's first state (both read the one shared
    `propagating_states()` helper, so a disagreement means that helper is
    being called inconsistently), its measurement names must be unique, and
    every non-unate arc must end up measuring each output edge from *both*
    input-edge directions. That last one is the property the single-state
    sweep cannot have, so it is asserted rather than assumed.
  * the **report** -- `records/corner_states.report.json`, if recorded, must
    cover every (arc, state, output edge) at every ratified corner. Verdict
    printed, not asserted, as above; when both reports are present the
    per-arc worst-over-states is printed against the single-state record so
    the comparison is reproducible rather than transcribed.

    python3 verification/functional/test_arcs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import gen_functional as g  # noqa: E402

TT_LIB = ROOT / "sim" / "characterize" / "records" / "s5l_tt_1p20v_25c.lib"
REPORT = HERE / "records" / "corners.report.json"
RTL: dict = {}
STATE_REPORT = HERE / "records" / "corner_states.report.json"


def arc_key(a: dict) -> tuple[str, str, str]:
    return (a["cell"], a["output"], a["pin"])


def trig_edge(arc: dict, edge: str) -> str:
    """The input edge that drives output edge `edge` of `arc` in its state.

    The same expression `gen_functional.build_corner_measurements` bakes into
    the `.meas` line, so the unateness this test asserts over is the unateness
    the deck actually measures.
    """
    return "RISE" if (arc["out_on_rise"] == (edge == "r")) else "FALL"


def check_evaluator_against_rtl() -> int:
    """The evaluator that derives the arcs must reproduce the RTL truth tables.

    Both views now parse with the same shared parser, so this is a check of
    `gen_netlists.evaluate()` against the Verilog `gen_models.py` renders from
    the same parse tree, exhaustively, through iverilog. It also pins the
    committed `rtl/<cell>.v` to the catalog the arc list is derived from.
    """
    import compare

    rtl = compare.rtl_tables()
    if not rtl:
        raise SystemExit("no RTL truth tables; iverilog/vvp produced nothing")
    checked = 0
    global RTL
    RTL = rtl
    for c in g.cells():
        ins = c["inputs"]
        for o, expr in c["outputs"].items():
            node = g.expression(expr, ins)
            for k, vec in enumerate(g.vectors(len(ins))):
                want = rtl.get((c["name"], o, k))
                if want is None:
                    raise SystemExit(f"no RTL table for {c['name']}.{o}[{k}]")
                got = int(g.evaluate(node, dict(zip(ins, vec))))
                if got != want:
                    raise SystemExit(
                        f"evaluating {expr!r} disagrees with rtl/{c['name']}.v "
                        f"at vector {k} ({dict(zip(ins, vec))}): {got} != {want}")
                checked += 1
    return checked


def states_from_rtl(rtl: dict) -> dict[tuple[str, str, str], list[tuple[dict, bool]]]:
    """Every arc's propagating states, derived from the iverilog truth tables.

    An **independent** oracle for what `gen_functional.propagating_states()`
    returns. These tables come from `rtl/<cell>.v` elaborated by iverilog, so
    nothing on this path shares code with the arc enumeration under test.

    Without it the non-unateness assertion below is circular, and provably so:
    an earlier draft of this test derived "which arcs are non-unate" from the
    same `out_on_rise` field it was checking, and therefore *accepted* a
    non-unate arc flattened to unate -- the flattened arc simply dropped out
    of the set being checked. A negative control caught it. The oracle is the
    fix: the expected state list, including each state's output direction, is
    asserted against the RTL rather than against itself.
    """
    out = {}
    for c in g.cells():
        ins = c["inputs"]
        n = len(ins)
        for o in c["outputs"]:
            for p in ins:
                rest = [q for q in ins if q != p]
                found = []
                for k in range(1 << len(rest)):
                    v = {q: bool((k >> (len(rest) - 1 - b)) & 1)
                         for b, q in enumerate(rest)}

                    def vector(pin_high: bool, v=v, p=p, ins=ins, n=n) -> int:
                        bits = {**v, p: pin_high}
                        return sum(int(bits[q]) << (n - 1 - j)
                                   for j, q in enumerate(ins))

                    try:
                        lo = rtl[(c["name"], o, vector(False))]
                        hi = rtl[(c["name"], o, vector(True))]
                    except KeyError as exc:
                        raise SystemExit(
                            f"no RTL table entry for {c['name']}.{o} {exc}")
                    if lo != hi:
                        found.append((v, bool(hi)))
                out[(c["name"], o, p)] = found
    return out


def check_arcs_against_liberty(arcs: list[dict]) -> None:
    """One arc per `timing ()` group of the recorded TT Liberty, no gaps."""
    gaps = [a for a in arcs if a["side"] is None]
    if gaps:
        raise SystemExit("arcs with no propagating state (declared gaps): "
                         + ", ".join(f"{a['cell']}.{a['pin']}->{a['output']}"
                                     for a in gaps))
    cells = {c["name"] for c in g.cells()}
    covered = {a["cell"] for a in arcs}
    if covered != cells:
        raise SystemExit(f"arcs cover {len(covered)} cells, not all {len(cells)}: "
                         f"missing {sorted(cells - covered)}")
    groups = len(re.findall(r"^\s*timing \(\)", TT_LIB.read_text(), re.M))
    if groups != len(arcs):
        raise SystemExit(
            f"{len(arcs)} derived arcs but {groups} `timing ()` groups in "
            f"{TT_LIB.relative_to(ROOT)}: the sweep and the characterized "
            "Liberty disagree about which arcs exist")


def check_arc_states(arcs: list[dict], states: list[dict],
                     rtl: dict) -> None:
    """The all-state enumeration against the RTL oracle and against `arcs()`.

    Asserts, in order: `arc_states()` reproduces the oracle's state list for
    every arc -- the states themselves *and* each one's output direction; it
    covers exactly the arcs `arcs()` does and starts each from the state
    `arcs()` measures; its measurement names are unique; and for every arc the
    oracle calls non-unate, the sweep measures each output edge from both
    input-edge directions. That last property is what the single-state sweep
    cannot have, so it is asserted, not assumed.
    """
    oracle = states_from_rtl(rtl)
    by_arc: dict[tuple[str, str, str], list[dict]] = {}
    for s in states:
        by_arc.setdefault(arc_key(s), []).append(s)

    if set(by_arc) != set(oracle):
        raise SystemExit(
            "arc_states() and the RTL oracle disagree about which arcs exist: "
            f"{sorted(set(by_arc) ^ set(oracle))[:5]}")
    if set(by_arc) != {arc_key(a) for a in arcs}:
        raise SystemExit(
            "arc_states() and arcs() disagree about which arcs exist: "
            f"{sorted(set(by_arc) ^ {arc_key(a) for a in arcs})[:5]}")

    for k, want in oracle.items():
        got = by_arc[k]
        if not want:
            if len(got) != 1 or got[0]["side"] is not None:
                raise SystemExit(f"{k} propagates in no state per the RTL, so "
                                 f"it must appear once as a declared gap; got "
                                 f"{len(got)} entries")
            continue
        if [(s["side"], s["out_on_rise"]) for s in got] != want:
            raise SystemExit(
                f"{k}: arc_states() yields "
                f"{[(g.held_tag(s), s['out_on_rise']) for s in got]} but the "
                f"iverilog RTL truth tables give "
                f"{[({q: int(b) for q, b in v.items()}, h) for v, h in want]}")
        if [s["state_index"] for s in got] != list(range(len(got))):
            raise SystemExit(f"{k} has state indices "
                             f"{[s['state_index'] for s in got]}, not 0..n-1")
        if any(s["state_count"] != len(want) for s in got):
            raise SystemExit(f"{k} disagrees about its state count")

    for a in arcs:
        got = by_arc[arc_key(a)]
        if got[0]["side"] != a["side"] or got[0]["out_on_rise"] != a["out_on_rise"]:
            raise SystemExit(
                f"{arc_key(a)}: arcs() measures state {a['side']} but "
                f"arc_states()[0] is {got[0]['side']} -- the two enumerations "
                "are not reading the same propagating_states() order")
        if a["state_count"] != len(oracle[arc_key(a)]):
            raise SystemExit(f"{arc_key(a)}: arcs() reports "
                             f"{a['state_count']} propagating states, the RTL "
                             f"gives {len(oracle[arc_key(a)])}")

    names = [g.arc_state_meas_name(s, e) for s in states
             if s["side"] is not None for e in ("r", "f")]
    if len(names) != len(set(names)):
        dupes = sorted({n for n in names if names.count(n) > 1})
        raise SystemExit(f"all-state measurement names collide: {dupes[:5]}")

    nonunate = sorted(k for k, v in oracle.items() if len({h for _, h in v}) > 1)
    if not nonunate:
        raise SystemExit("the RTL oracle finds no non-unate arc; this library "
                         "has mux and xor cells, so that cannot be right")
    for k in nonunate:
        for edge in ("r", "f"):
            dirs = {trig_edge(s, edge) for s in by_arc[k]}
            if dirs != {"RISE", "FALL"}:
                raise SystemExit(
                    f"non-unate arc {k} measures its {edge} output edge from "
                    f"{sorted(dirs)} only; covering every state must give both")
    multi = [k for k, v in by_arc.items() if len(v) > 1]
    print(f"ok: {len(states)} (arc, state) pairs over {len(by_arc)} arcs "
          f"({len(multi)} multi-state, {len(nonunate)} non-unate), every state "
          f"and its output direction matching the iverilog RTL truth tables; "
          f"{len(names)} unique delay names; every non-unate arc measures both "
          f"output edges from both input-edge directions")


def check_state_report(states: list[dict]) -> None:
    """Coverage and shape of the all-state report. Verdict printed, not asserted."""
    report = json.loads(STATE_REPORT.read_text())
    want = {g.arc_state_meas_name(s, e) for s in states
            if s["side"] is not None for e in ("r", "f")}
    rollup = {m["name"]: m for m in report["measurements"]}
    if set(rollup) != want:
        raise SystemExit(
            f"all-state report measures {len(rollup)} names, expected "
            f"{len(want)}: missing {sorted(want - set(rollup))[:5]}, "
            f"unexpected {sorted(set(rollup) - want)[:5]}")
    for name, m in rollup.items():
        if not m.get("limits", {}).get("max"):
            raise SystemExit(f"{name} carries no limits.max")
        if m.get("spec_row") != g.SPEC_ROW:
            raise SystemExit(f"{name} is not tagged spec_row {g.SPEC_ROW!r}")

    corner_ids = [c["corner_id"] for c in report["corners"]]
    if len(corner_ids) != len(g.char.CORNERS):
        raise SystemExit(f"all-state report has corners {corner_ids}, expected "
                         f"one per ratified corner ({list(g.char.CORNERS)})")
    for corner in report["corners"]:
        names = {m["name"] for m in corner["measurements"]}
        if names != want:
            raise SystemExit(f"corner {corner['corner_id']} measures "
                             f"{len(names)} of {len(want)} (arc, state, edge) "
                             f"triples: missing {sorted(want - names)[:5]}")

    print(f"all-state report: status {report['status']}, {len(corner_ids)} "
          f"corners ({', '.join(corner_ids)}), {len(want)} delays each, "
          f"limit {g.LIMIT_NS} ns, batch job "
          f"{report.get('environment', {}).get('remote', {}).get('job_id')}")
    for corner in report["corners"]:
        bad = [m["name"] for m in corner["measurements"] if m["status"] != "pass"]
        print(f"  {corner['corner_id']}: {corner['status']}, "
              f"{len(corner['measurements']) - len(bad)}/{len(want)} pass"
              + (f"; over the bound: {', '.join(bad)}" if bad else ""))
    if REPORT.exists():
        print_state_comparison(states, report, json.loads(REPORT.read_text()))


def print_state_comparison(states: list[dict], state_report: dict,
                           single_report: dict) -> None:
    """What measuring every state changed, per corner. Printed, never asserted.

    Two spreads, kept apart on purpose, because only one of them is a property
    of the library:

      * the **state spread** -- for each multi-state arc edge, the worst delay
        over its states against that same arc's *first* state, both taken from
        this one all-state run. Same job, same deck, same environment, so the
        difference is the side-input state and nothing else. This is the number
        the single-state sweep could not see.
      * the **run-to-run spread** -- the same delay for every *single*-state
        arc, this run against `corners.report.json`. Those arcs have one state,
        so any difference between the two records is numerical: a larger deck
        means a different matrix and a different adaptive timestep. It is
        printed as the floor under which a state spread is not a real effect.

    Also named: which delays are over the bound, and whether that set differs
    from the single-state record's (an arc that passed single-state and fails
    here is a finding, not a tolerance).
    """
    by_arc: dict[tuple[str, str, str], list[dict]] = {}
    for s in states:
        if s["side"] is not None:
            by_arc.setdefault(arc_key(s), []).append(s)
    limit_s = g.LIMIT_NS * 1e-9
    for corner in state_report["corners"]:
        cid = corner["corner_id"]
        vals = {m["name"]: m["value"] for m in corner["measurements"]}
        single = next((c for c in single_report["corners"]
                       if c["corner_id"] == cid), None)
        over = sorted(m["name"] for m in corner["measurements"]
                      if m["value"] is not None and m["value"] > limit_s)
        print(f"  {cid}: {len(over)} of {len(corner['measurements'])} delays "
              f"over the {g.LIMIT_NS} ns bound")

        spread, noise = [], []
        for k, group in by_arc.items():
            for edge in ("r", "f"):
                got = [(vals[g.arc_state_meas_name(s, edge)], s) for s in group
                       if vals.get(g.arc_state_meas_name(s, edge)) is not None]
                if len(got) != len(group):
                    continue
                worst, s = max(got, key=lambda x: x[0])
                first = next(v for v, q in got if q["state_index"] == 0)
                if len(group) > 1:
                    spread.append((worst - first, worst, first, k, edge, s))
                elif single is not None:
                    was = {m["name"]: m["value"]
                           for m in single["measurements"]}.get(
                               g.arc_meas_name(group[0], edge))
                    if was is not None:
                        noise.append((abs(worst - was), k, edge))
        print(f"    state spread over {len(spread)} multi-state arc edges "
              f"(worst state vs. this run's first state):")
        for d, worst, first, k, edge, s in sorted(spread, reverse=True)[:10]:
            print(f"      {k[0]} {k[2]}->{k[1]} {edge}: {first * 1e9:.4f} -> "
                  f"{worst * 1e9:.4f} ns (+{d * 1e9:.4f}) holding "
                  f"{g.held_tag(s) or '(single input)'}, margin "
                  f"{(limit_s - worst) * 1e9:+.4f} ns")
        if spread:
            print(f"      largest state spread {max(spread)[0] * 1e9:+.4f} ns; "
                  f"{sum(1 for x in spread if x[0] > 0)} of {len(spread)} arc "
                  "edges are slowest in a state the single-state sweep skipped")
        if noise:
            print(f"    run-to-run spread on the {len(noise)} single-state arc "
                  f"edges vs. corners.report.json: max "
                  f"{max(noise)[0] * 1e9:.4f} ns on "
                  f"{max(noise)[1][0]} {max(noise)[1][2]}->{max(noise)[1][1]} "
                  f"{max(noise)[2]} -- these arcs have one state, so this is "
                  "the numerical floor, not an effect")
        if single is None:
            print(f"    {cid} is not in the single-state record; no comparison")
            continue
        was_over = sorted(m["name"] for m in single["measurements"]
                          if m["value"] is not None and m["value"] > limit_s)
        was_arcs = {n.rsplit("_", 1)[0] for n in was_over}
        now_arcs = {g.arc_meas_name(by_arc[arc_key(s)][0], n.rsplit("_", 1)[1])
                    .rsplit("_", 1)[0]
                    for n in over
                    for s in states
                    if s["side"] is not None
                    and g.arc_state_meas_name(s, n.rsplit("_", 1)[1]) == n}
        print(f"    over the bound here: {', '.join(over) or 'none'}")
        if now_arcs - was_arcs:
            print(f"    NEW over the bound, passed single-state: "
                  f"{', '.join(sorted(now_arcs - was_arcs))}")
        elif was_arcs - now_arcs:
            print(f"    over the bound single-state but not here: "
                  f"{', '.join(sorted(was_arcs - now_arcs))}")
        else:
            print("    same arcs over the bound as the single-state record")


def check_report(arcs: list[dict]) -> None:
    """Shape of the recorded corner report. Verdict is printed, not asserted."""
    report = json.loads(REPORT.read_text())
    want = {g.arc_meas_name(a, e) for a in arcs for e in ("r", "f")}
    rollup = {m["name"]: m for m in report["measurements"]}
    if set(rollup) != want:
        raise SystemExit(f"report measures {len(rollup)} names, expected "
                         f"{len(want)}: missing {sorted(want - set(rollup))[:5]}")
    for name, m in rollup.items():
        if not m.get("limits", {}).get("max"):
            raise SystemExit(f"{name} carries no limits.max")
        if m.get("spec_row") != g.SPEC_ROW:
            raise SystemExit(f"{name} is not tagged spec_row {g.SPEC_ROW!r}")

    corner_ids = [c["corner_id"] for c in report["corners"]]
    if len(corner_ids) != len(g.char.CORNERS):
        raise SystemExit(f"report has corners {corner_ids}, expected one per "
                         f"ratified corner ({list(g.char.CORNERS)})")
    for corner in report["corners"]:
        names = {m["name"] for m in corner["measurements"]}
        if names != want:
            raise SystemExit(f"corner {corner['corner_id']} measures "
                             f"{len(names)} of {len(want)} arcs: missing "
                             f"{sorted(want - names)[:5]}")

    limit_s = g.LIMIT_NS * 1e-9
    worst = max(
        ((m["value"], m["name"], c["corner_id"])
         for c in report["corners"] for m in c["measurements"]
         if m.get("value") is not None),
        default=None)
    print(f"report: status {report['status']}, {len(corner_ids)} corners "
          f"({', '.join(corner_ids)}), {len(want)} arc delays each, "
          f"limit {g.LIMIT_NS} ns")
    if worst:
        print(f"  worst arc: {worst[1]} at {worst[2]} = {worst[0] * 1e9:.4f} ns "
              f"(margin {(limit_s - worst[0]) * 1e9:+.4f} ns)")
    for corner in report["corners"]:
        bad = [m["name"] for m in corner["measurements"] if m["status"] != "pass"]
        print(f"  {corner['corner_id']}: {corner['status']}, "
              f"{len(corner['measurements']) - len(bad)}/{len(want)} arcs pass"
              + (f"; over the bound: {', '.join(bad)}" if bad else ""))


def main() -> int:
    arcs = g.arcs()
    states = g.arc_states()
    checked = check_evaluator_against_rtl()
    print(f"ok: the shared parser's evaluator matches the RTL truth tables on "
          f"{checked} vectors")
    check_arcs_against_liberty(arcs)
    print(f"ok: {len(arcs)} arcs, 0 gaps, all {len(g.cells())} cells, one per "
          f"`timing ()` group of the recorded TT Liberty")
    check_arc_states(arcs, states, RTL)
    if REPORT.exists():
        check_report(arcs)
    else:
        print(f"skip: {REPORT.relative_to(ROOT)} not recorded yet")
    if STATE_REPORT.exists():
        check_state_report(states)
    else:
        print(f"skip: {STATE_REPORT.relative_to(ROOT)} not recorded yet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
