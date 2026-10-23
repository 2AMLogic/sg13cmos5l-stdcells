# 0001 — Ratify the target specification

- **Status**: accepted
- **Date**: 2026-10-17
- **Issue**: #2

## Context

The README target table was a proposal mirroring `sg13g2-stdcells`, whose own
spec is still a draft (origin commit `f450813c6a5eecf3cf67aaf899db90d11f4ee68c`
has a placeholder `spec/` and no decision records). Nothing downstream can be
verified against a row until it is ratified. The repo rule is that the PDK
comparison comes from PDK documentation, not assumption.

## Decision

Ratify [`target-spec.md`](../target-spec.md) as the target specification, on
the evidence in [`pdk-comparison.md`](../pdk-comparison.md).

Every inherited row is **confirmed**. Changes to the proposal:

1. **Row-height fallback made concrete**: "as `sg13cmos5l_stdcell`" becomes
   3.78 µm (9 tracks), read from the baseline LEF `CoreSite` (0.48 × 3.78 µm).
   Reason: the baseline is 12.5 % taller than the 3.36 µm target, which the
   PDK documents do not show to be reachable.
2. **Core supply stated**: 1.20 V, with FF 1.32 V and SS 1.08 V. The baseline's
   1.5 V family is explicitly out of scope.
3. **Characterization grid added**: the baseline's 7 × 7 delay index set.
4. **Benchmark energy row carried** from the origin (≤ 1.00×, stretch ≤ 0.80×).
5. **Benchmark designs and flow stated**: the PDK's open LibreLane flow, same
   on both libraries; designs must be mappable without sequential cells.
6. **README**: DRAFT marker removed; citation corrected from issue #1 to #2.

## Consequences

- Three confirmed rows carry a stated risk, not a verified result: row height
  (3.36 µm feasibility), routing grid (0.42 µm pins against 0.48 µm Metal2/4
  tracks), and DRC/LVS (deck coverage, deferred to #4). No row is relaxed to
  make a result pass; the only permitted relaxation, row height to 3.78 µm,
  requires a new record citing generator evidence.
- The benchmark is blocked on Liberty writing and on sequential cells (both
  deferred with the origin); until then no benchmark claim is made.
- No generator gap is filed upstream because no generator exists to show one;
  the check is repeated when the first generator is pinned.
- Reuse is by pin (`reuse.lock.json`, issue #3), never a fork.
- If the origin later ratifies or changes a row, the matching row is
  re-checked by a new record.

## Alternatives rejected

- **Ratify the origin table verbatim with a "confirm later" note**: violates the
  rule that the PDK comparison precedes ratification.
- **Run `klt drc`/`klt lvs` here to answer the coverage question**: that is
  issue #4's smoke run; this spec records it as deferred.
- **Change the target row height to 3.78 µm to match the baseline**: the PDK
  documents give no reason 3.36 µm is unreachable, and a target is not relaxed
  without evidence.
