#!/usr/bin/env bash
# Regenerate the klt signoff output and fail if it differs from the committed
# record, then re-check the committed T1 attestation envelopes. Used by CI
# (.github/workflows/ci.yml) and `npm run check:signoff` — CI runs this script,
# so the two cover the same checks.
#
# klt is fetched at the repo's one pin of record, layout/toolchain.json
# (klt.install_spec): no host-wide tool is touched, and no klt version literal
# lives in this script or in the workflow. Needs `uvx` (uv) on PATH.
#
# Usage:
#   scripts/check_signoff.sh                check the record and the envelopes
#   scripts/check_signoff.sh --regenerate   rewrite the committed signoff record
set -uo pipefail

usage() {
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
}

regenerate=0
case "${1:-}" in
  "") ;;
  --regenerate) regenerate=1 ;;
  -h | --help)
    usage
    exit 0
    ;;
  *)
    echo "error: unknown argument: $1 (try --help)" >&2
    exit 2
    ;;
esac

cd "$(dirname "$0")/.." || exit 1

RECORD="manifests/sg13cmos5l-stdcells.signoff.json"

# The pin of record. Never copy the version here: a second copy is what drifted
# (issue #112) when layout/toolchain.json moved from 0.8.0 to 0.9.1.
KLT_SPEC="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1]))["klt"]["install_spec"])' layout/toolchain.json)"
if [ -z "${KLT_SPEC:-}" ]; then
  echo "error: cannot read klt.install_spec from layout/toolchain.json" >&2
  exit 1
fi

fresh="$(mktemp)"
trap 'rm -f "$fresh"' EXIT

rc=0
uvx --from "$KLT_SPEC" klt signoff \
  --manifest manifests/sg13cmos5l-stdcells.json \
  --tiers-doc manifests/design-evidence-tiers.md \
  --format json > "$fresh" || rc=$?
# 0 = every T1 item met; 3 = grader ran clean, some item unmet. Both are valid.
if [ "$rc" -ne 0 ] && [ "$rc" -ne 3 ]; then
  echo "error: klt signoff exited $rc (expected 0 or 3): manifest or tiers doc is broken" >&2
  exit 1
fi

if [ "$regenerate" -eq 1 ]; then
  cp "$fresh" "$RECORD"
  echo "ok: regenerated $RECORD with $KLT_SPEC (commit it in the same PR)"
  exit 0
fi

if ! cmp -s "$fresh" "$RECORD"; then
  echo "error: fresh klt signoff output differs from $RECORD" >&2
  echo "Regenerate and commit it in the same PR: scripts/check_signoff.sh --regenerate" >&2
  diff <(python3 -m json.tool "$fresh") \
       <(python3 -m json.tool "$RECORD") >&2 || true
  exit 1
fi
echo "ok: committed signoff record matches a fresh $KLT_SPEC run"

# The committed attestation envelopes are the evidence the manifest cites for
# items 9 and 10. CI used to re-check them with its own version literal; they
# run here instead, at the same pin.
attest_rc=0
echo "--- re-checking the item-9 testbench attestation"
uvx --from "$KLT_SPEC" klt signoff --attest 9 \
  --inventory sim/attest/item9.inventory.json \
  --check sim/attest/item9.envelope.json || attest_rc=1
echo "--- re-checking the item-10 repo-hygiene attestation"
uvx --from "$KLT_SPEC" klt signoff --attest 10 \
  --inventory manifests/item-10-inventory.json \
  --check manifests/evidence/item-10-repo-hygiene.json || attest_rc=1

if [ "$attest_rc" -ne 0 ]; then
  echo "error: an attestation re-check failed: re-attest and commit the envelope" >&2
  echo "(see manifests/README.md), then regenerate the signoff record." >&2
  exit 1
fi
echo "ok: item-9 and item-10 attestation envelopes re-check clean under $KLT_SPEC"
