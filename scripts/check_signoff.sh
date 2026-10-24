#!/usr/bin/env bash
# Regenerate the klt signoff output and fail if it differs from the committed
# record. Used by CI (.github/workflows/ci.yml) and `npm run check:signoff`.
# Needs `uvx` (uv) on PATH; klt is fetched at the pinned release, so no
# host-wide tool is touched.
set -uo pipefail

KLT_PIN="0.7.0"   # keep in step with manifests/README.md and the committed record

cd "$(dirname "$0")/.."
fresh="$(mktemp)"
trap 'rm -f "$fresh"' EXIT

rc=0
uvx --from "klayout-tools==${KLT_PIN}" klt signoff \
  --manifest manifests/sg13cmos5l-stdcells.json \
  --tiers-doc manifests/design-evidence-tiers.md \
  --format json > "$fresh" || rc=$?
# 0 = every T1 item met; 3 = grader ran clean, some item unmet. Both are valid.
if [ "$rc" -ne 0 ] && [ "$rc" -ne 3 ]; then
  echo "error: klt signoff exited $rc (expected 0 or 3): manifest or tiers doc is broken" >&2
  exit 1
fi
if ! cmp -s "$fresh" manifests/sg13cmos5l-stdcells.signoff.json; then
  echo "error: fresh klt signoff output differs from manifests/sg13cmos5l-stdcells.signoff.json" >&2
  echo "Regenerate and commit it in the same PR (see manifests/README.md)." >&2
  diff <(python3 -m json.tool "$fresh") \
       <(python3 -m json.tool manifests/sg13cmos5l-stdcells.signoff.json) >&2 || true
  exit 1
fi
echo "ok: committed signoff record matches a fresh klt ${KLT_PIN} run"
