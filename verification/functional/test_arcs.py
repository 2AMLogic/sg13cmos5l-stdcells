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

Every assertion over the all-state sweep carries a committed negative control
that proves it still bites (issue #148). They run in-process over deep copies
of the enumeration and of the parsed report, so no control writes to, doctors,
or restores any committed record:

    python3 verification/functional/test_arcs.py
    python3 verification/functional/test_arcs.py --negative-control
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import re
import sys
from pathlib import Path
from typing import Callable, NamedTuple

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
            dirs = {g.trig_edge(s, edge) for s in by_arc[k]}
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


def check_state_report(states: list[dict], report: dict) -> None:
    """Coverage and shape of the all-state report. Verdict printed, not asserted.

    Takes the parsed report rather than reading `STATE_REPORT` itself, which is
    the whole seam the report-side negative controls need: a control injects a
    mutated copy in memory instead of doctoring the committed record on disk
    and restoring it afterwards (issue #148).
    """
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


# ---------------------------------------------------------------------------
# Negative controls for the all-state assertions (issue #148)
#
# PR #146 added `check_arc_states` and `check_state_report` and justified them
# with negative controls reported in its description and committed nowhere, so
# nothing re-checked that the assertions still bit after a later edit. These
# are those controls, re-derived and committed, in the shape this directory
# already uses for `compare.py --negative-control`.
#
# A control that merely makes a check exit nonzero is not enough. Four of the
# five enumeration controls are caught by the *same* assertion -- the oracle
# state-list comparison -- so a mutation can be rejected for the wrong reason
# and still look green. Each control therefore declares the diagnosis it
# expects and is **failed** if a different assertion catches it. That is not
# hypothetical: the obvious way to build the name-collision control, by
# mutating `side`, is shadowed by the oracle comparison and asserts nothing
# about name uniqueness. `SHADOW_PROBE` below is that control, and the runner
# asserts it is reported as shadowed.
# ---------------------------------------------------------------------------
EXIT_CONTROL_QUIET = 1  # a control was not rejected by the assertion it names


class Control(NamedTuple):
    """One mutation that must be rejected by one named assertion.

    `expect` holds the substrings the diagnosis must contain; `mutate` returns
    any further ones it can only name once it has chosen its target (the arc it
    dropped a state from, the measurement it untagged), which is what keeps a
    control from being satisfied by the right assertion firing about the wrong
    arc. `reproduces` names the silent failure mode the mutation stands for,
    in the style of `sim/harness/corners.py`'s `sabotage()`.
    """

    name: str
    target: str  # "enumeration" (mutate arc_states()) | "report" (inject one)
    assertion: str
    reproduces: str
    expect: tuple[str, ...]
    mutate: Callable[..., tuple[str, ...]]


def _group(states: list[dict], k: tuple[str, str, str]) -> list[dict]:
    return [s for s in states if arc_key(s) == k]


def _first_multi_state(states: list[dict]) -> tuple[str, str, str]:
    """The first arc with more than one propagating state, in enumeration order."""
    seen: dict[tuple[str, str, str], int] = {}
    for s in states:
        seen[arc_key(s)] = seen.get(arc_key(s), 0) + 1
    for k, n in seen.items():
        if n > 1:
            return k
    raise SystemExit("no multi-state arc to mutate: the enumeration controls "
                     "assume this library has at least one")


def _first_nonunate(ctx: dict) -> tuple[str, str, str]:
    """The first arc the RTL oracle calls non-unate, by sorted arc key."""
    nonunate = sorted(k for k, v in ctx["oracle"].items()
                      if len({h for _, h in v}) > 1)
    if not nonunate:
        raise SystemExit("the RTL oracle finds no non-unate arc to flatten")
    return nonunate[0]


# --- enumeration-side mutations: the states list, never the RTL oracle -----

def _drop_state(states: list[dict], ctx: dict) -> tuple[str, ...]:
    k = _first_multi_state(states)
    states.remove(_group(states, k)[-1])
    return (f"{k}: arc_states() yields",)


def _flatten_nonunate(states: list[dict], ctx: dict) -> tuple[str, ...]:
    k = _first_nonunate(ctx)
    for s in _group(states, k):
        s["out_on_rise"] = True
    return (f"{k}: arc_states() yields",)


def _invert_directions(states: list[dict], ctx: dict) -> tuple[str, ...]:
    for s in states:
        if s["out_on_rise"] is not None:
            s["out_on_rise"] = not s["out_on_rise"]
    return ()


def _swap_states(states: list[dict], ctx: dict) -> tuple[str, ...]:
    k = _first_multi_state(states)
    a, b = _group(states, k)[:2]
    # Swap the two states but leave `state_index` alone, so the index run
    # 0..n-1 still holds and only the enumeration *order* has moved -- the
    # index check must not be what catches this.
    a["side"], b["side"] = b["side"], a["side"]
    a["out_on_rise"], b["out_on_rise"] = b["out_on_rise"], a["out_on_rise"]
    return (f"{k}: arc_states() yields",)


def _collide_names(states: list[dict], ctx: dict) -> tuple[str, ...]:
    k = _first_multi_state(states)
    group = _group(states, k)
    # Truncate only `side_order`, which the oracle state-list comparison does
    # not read, so this reaches the name-collision check. Mutating `side`
    # instead would collide the names too but be rejected by the oracle
    # comparison first -- see SHADOW_PROBE.
    for s in group:
        s["side_order"] = []
    return (g.arc_state_meas_name(group[0], "f"),)


def _collide_names_via_side(states: list[dict], ctx: dict) -> tuple[str, ...]:
    k = _first_multi_state(states)
    group = _group(states, k)
    group[1]["side"] = dict(group[0]["side"])
    return ()


# --- report-side mutations: a parsed copy, never the file on disk ----------

def _drop_triple_at_ss(report: dict, ctx: dict) -> tuple[str, ...]:
    corner = next(c for c in report["corners"]
                  if c["corner_id"].startswith("ss"))
    # Drop the lexicographically first name so it is inside the diagnosis's
    # truncated `missing [...]` head and this control can require it by name.
    gone = min(corner["measurements"], key=lambda m: m["name"])
    corner["measurements"].remove(gone)
    return (f"corner {corner['corner_id']} measures", gone["name"])


def _drop_spec_row(report: dict, ctx: dict) -> tuple[str, ...]:
    m = report["measurements"][0]
    del m["spec_row"]
    return (m["name"],)


def _empty_limits(report: dict, ctx: dict) -> tuple[str, ...]:
    m = report["measurements"][0]
    m["limits"] = {}
    return (m["name"],)


def _drop_corner(report: dict, ctx: dict) -> tuple[str, ...]:
    report["corners"] = [c for c in report["corners"]
                         if not c["corner_id"].startswith("ss")]
    return ()


_ORACLE_CMP = ("arc_states() yields", "iverilog RTL truth tables give")

CONTROLS: tuple[Control, ...] = (
    Control(
        name="dropped_state",
        target="enumeration",
        assertion="the oracle state-list comparison in check_arc_states",
        reproduces="arc_states() stops emitting one of a multi-state arc's "
                   "states, so the sweep silently measures fewer states than "
                   "propagate the arc",
        expect=_ORACLE_CMP,
        mutate=_drop_state,
    ),
    Control(
        name="unate_flattening",
        target="enumeration",
        assertion="the oracle state-list comparison in check_arc_states",
        reproduces="a non-unate arc's states all claim the same output "
                   "direction, which is the mutation an earlier draft of this "
                   "test accepted because it derived non-unateness from the "
                   "same out_on_rise field it was checking",
        expect=_ORACLE_CMP,
        mutate=_flatten_nonunate,
    ),
    Control(
        name="inverted_directions",
        target="enumeration",
        assertion="the oracle state-list comparison in check_arc_states",
        reproduces="every state's out_on_rise is inverted, so the deck "
                   "measures each delay from the wrong input edge",
        expect=_ORACLE_CMP,
        mutate=_invert_directions,
    ),
    Control(
        name="swapped_states",
        target="enumeration",
        assertion="the oracle state-list comparison in check_arc_states",
        reproduces="two states of one arc come out of propagating_states() "
                   "order, so state_index no longer names the state the "
                   "report's measurement name says it holds",
        expect=_ORACLE_CMP,
        mutate=_swap_states,
    ),
    Control(
        name="name_collision",
        target="enumeration",
        assertion="the measurement-name uniqueness check in check_arc_states",
        reproduces="two states of one arc produce the same .meas name, so one "
                   "silently overwrites the other in the report and a state "
                   "goes unmeasured while the count still looks right",
        expect=("all-state measurement names collide",),
        mutate=_collide_names,
    ),
    Control(
        name="missing_triple_at_ss",
        target="report",
        assertion="the per-corner coverage loop in check_state_report",
        reproduces="one (arc, state, output edge) is absent at the slow "
                   "corner, so the worst-case corner bounds one delay fewer "
                   "than the rollup claims",
        expect=("(arc, state, edge) triples: missing",),
        mutate=_drop_triple_at_ss,
    ),
    Control(
        name="missing_spec_row",
        target="report",
        assertion="the spec_row tag check in check_state_report",
        reproduces="a measurement is not tagged with the spec row it bounds, "
                   "so it is evidence for nothing the spec asked for",
        expect=("is not tagged spec_row",),
        mutate=_drop_spec_row,
    ),
    Control(
        name="missing_limits_max",
        target="report",
        assertion="the limits.max check in check_state_report",
        reproduces="a measurement carries no upper bound, so `klt sim` grades "
                   "it no_limits_checked and its pass verdict means nothing",
        expect=("carries no limits.max",),
        mutate=_empty_limits,
    ),
    Control(
        name="missing_corner",
        target="report",
        assertion="the corner-count check in check_state_report",
        reproduces="a ratified corner is absent from the report, so the "
                   "all-state claim covers fewer corners than the spec "
                   "ratified",
        expect=("all-state report has corners",
                "expected one per ratified corner"),
        mutate=_drop_corner,
    ),
)

SHADOW_PROBE = Control(
    name="name_collision_via_side",
    target="enumeration",
    assertion="the measurement-name uniqueness check -- which it never reaches",
    reproduces="the name-collision control built the obvious way, by mutating "
               "`side`: the oracle state-list comparison rejects it first, so "
               "it looks green while asserting nothing about name uniqueness",
    expect=("all-state measurement names collide",),
    mutate=_collide_names_via_side,
)


def control_context() -> dict:
    """The honest inputs every control mutates a deep copy of.

    The iverilog oracle is built once and shared: it is 0.1 s of the 0.15 s a
    full pass costs, and every control needs an *unmutated* one -- the
    mutations are applied to the enumeration and to the parsed report, never
    to the RTL tables the assertions check them against.
    """
    import compare

    rtl = compare.rtl_tables()
    if not rtl:
        raise SystemExit("no RTL truth tables; iverilog/vvp produced nothing")
    if not STATE_REPORT.exists():
        raise SystemExit(
            f"{STATE_REPORT.relative_to(ROOT)} is not recorded, so the "
            "report-side controls have nothing to inject a mutated copy of; "
            "the controls read the committed record and never write one")
    return {"arcs": g.arcs(), "states": g.arc_states(), "rtl": rtl,
            "oracle": states_from_rtl(rtl),
            "report": json.loads(STATE_REPORT.read_text())}


def run_control(control: Control, ctx: dict) -> tuple[str, str]:
    """Apply one control to deep copies and classify what its check did.

    Returns one of three verdicts with the diagnosis that produced it:

      * ``rejected`` -- the check raised, and the diagnosis is the one this
        control declares. The only passing verdict.
      * ``shadowed`` -- the check raised, but with a different diagnosis: some
        other assertion caught the mutation first, so this control proves
        nothing about the one it targets.
      * ``quiet`` -- the check did not raise at all. The assertion this
        control targets has been deleted or weakened.
    """
    if control.target == "enumeration":
        subject = copy.deepcopy(ctx["states"])
        extra = control.mutate(subject, ctx)

        def call() -> None:
            check_arc_states(ctx["arcs"], subject, ctx["rtl"])
    else:
        subject = copy.deepcopy(ctx["report"])
        extra = control.mutate(subject, ctx)

        def call() -> None:
            check_state_report(ctx["states"], subject)

    want = [" ".join(w.split()) for w in (*control.expect, *extra)]
    try:
        # A check that fails to bite prints its "ok:" line; keep that out of
        # the control log, where it would read as a pass.
        with contextlib.redirect_stdout(io.StringIO()):
            call()
    except SystemExit as exc:
        diag = " ".join(str(exc.code).split())
        if all(w in diag for w in want):
            return "rejected", diag
        return "shadowed", diag
    return "quiet", ""


def run_negative_controls() -> int:
    """Run every control twice, then the shadow probe. Exit 0 only if all bite."""
    ctx = control_context()
    enum_n = sum(c.target == "enumeration" for c in CONTROLS)
    print(f"negative controls: {len(CONTROLS)} mutations over the all-state "
          f"assertions -- {enum_n} of the enumeration (check_arc_states) and "
          f"{len(CONTROLS) - enum_n} of the recorded report "
          f"(check_state_report). Each must be rejected by the assertion it "
          f"names, not merely rejected.")
    first = [run_control(c, ctx) for c in CONTROLS]
    # Run the whole table a second time in the same process: every control
    # mutates a deep copy, so a control that leaked into the shared inputs
    # would change another's verdict here.
    again = [run_control(c, ctx) for c in CONTROLS]

    failed = []
    for c, (verdict, diag) in zip(CONTROLS, first):
        print(f"  {verdict:8} {c.name:21} rejected by {c.assertion}"
              if verdict == "rejected" else
              f"  {verdict:8} {c.name:21} should be rejected by {c.assertion}")
        head = diag[:150] or "(no diagnosis: the check did not raise at all)"
        print(f"           {head}")
        if verdict != "rejected":
            failed.append((c, verdict, diag))

    sys.stdout.flush()  # keep every diagnosis below after the per-control log
    if first != again:
        drifted = [c.name for c, a, b in zip(CONTROLS, first, again) if a != b]
        print("FAIL: controls leaked into one another -- a second pass in the "
              f"same process changed the verdict of {drifted}", file=sys.stderr)
        return EXIT_CONTROL_QUIET
    print(f"  ok: the same {len(CONTROLS)} verdicts on a second pass in this "
          "process, so no control leaks into another's inputs")

    # The shadow probe: the name-collision control built the obvious way must
    # be reported as shadowed, which is what proves the per-control diagnosis
    # match above is doing work rather than accepting any nonzero exit.
    probe, probe_diag = run_control(SHADOW_PROBE, ctx)
    if probe != "shadowed":
        print(f"FAIL: the shadow probe ({SHADOW_PROBE.name}) was reported "
              f"{probe!r}, expected 'shadowed'. It mutates `side`, which the "
              "oracle state-list comparison reads, so it must be caught there "
              "and not by the name-collision check it nominally targets; a "
              "runner that reports it rejected is accepting any nonzero exit "
              f"as proof. Diagnosis: {probe_diag[:200]}", file=sys.stderr)
        return EXIT_CONTROL_QUIET
    print(f"  ok: shadow probe {SHADOW_PROBE.name} is reported shadowed, not "
          "rejected -- it is caught by the oracle state-list comparison "
          "before the name-collision check it targets, so it would prove "
          "nothing about name uniqueness")

    if failed:
        for c, verdict, diag in failed:
            why = ("was caught by a different assertion, so it proves nothing "
                   "about the one it targets"
                   if verdict == "shadowed" else
                   "did not fail at all: the assertion it targets is gone or "
                   "weakened")
            print(f"control: {c.name} {why}. It reproduces: {c.reproduces}. "
                  f"Expected a diagnosis containing {list(c.expect)}, got "
                  f"{diag[:200]!r}", file=sys.stderr)
        print(f"control: {len(failed)} of {len(CONTROLS)} negative controls "
              "did not bite; the all-state assertions no longer hold the "
              "ground they are credited with", file=sys.stderr)
        return EXIT_CONTROL_QUIET
    print(f"ok: all {len(CONTROLS)} negative controls rejected, each by the "
          "assertion it names")
    return 0


def run_checks() -> int:
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
        check_state_report(states, json.loads(STATE_REPORT.read_text()))
    else:
        print(f"skip: {STATE_REPORT.relative_to(ROOT)} not recorded yet")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Checks for the corner-matrix timing-arc evidence.")
    ap.add_argument("--checks", action="store_true",
                    help="run the normal pass (the default when no mode is "
                         "given)")
    ap.add_argument("--negative-control", action="store_true",
                    help="run only the committed negative controls: every "
                         "mutation must be rejected by the assertion it names")
    args = ap.parse_args(argv)
    if args.checks and args.negative_control:
        ap.error("--checks cannot be combined with --negative-control: a "
                 "control run asserts that the checks *fail* on a deliberately "
                 "mutated copy, so a zero exit there means the opposite of "
                 "what it means for a normal pass, and one process must not "
                 "report both under one status")
    if args.negative_control:
        return run_negative_controls()
    return run_checks()


if __name__ == "__main__":
    sys.exit(main())
