#!/usr/bin/env bash
# Cold-start command for the T1 item-9 testbench attestation (issue #31):
# bring a clean clone to a runnable state, then run each committed smoke bench
# on its single-corner tt probe request, locally. The five-corner requests
# (sim/smoke/inverter_*.request.json) run on the batch fleet and are recorded
# under sim/smoke/records/, so they are not part of a cold start that has to
# reproduce from a clean checkout alone. SIMULATED only.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
scripts/setup-env.sh
# shellcheck disable=SC1091
source .cache/env.sh
out="$(mktemp -d)"
trap 'rm -rf "$out"' EXIT
for bench in inverter_dc inverter_tran; do
    klt sim --backend local "sim/smoke/records/$bench.tt-probe.request.json" \
        -o "$out/$bench" --report-out "$out/$bench.report.json"
done
