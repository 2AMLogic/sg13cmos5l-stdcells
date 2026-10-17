#!/usr/bin/env bash
# Bring a fresh clone to a runnable SG13CMOS5L state (issue #4): the pinned
# PDK, an OSDI-capable ngspice, the Verilog-A models built to OSDI, and klt at
# a pinned commit. Everything lands inside this checkout (gitignored pdks/,
# .cache/, .venv/); nothing is installed host-wide.
#
#   scripts/setup-env.sh          # idempotent; re-run is cheap
#   source .cache/env.sh          # PDK_ROOT, PDK, PATH for klt / ngspice / openvaf-r
#
# Pins: sim/pdk.json, sim/toolchain.json, layout/toolchain.json. Fails closed:
# any sha256 mismatch (klayout-tools fetch scripts, ngspice tarball, PDK
# tarball via the klayout-tools script), a pin that disagrees with the fetch
# script it drives, a dangling shared-model symlink the smoke bench needs, or
# an OSDI model that does not load aborts with a non-zero exit.
#
# Modest by design: the ngspice build uses `make -j${SETUP_JOBS:-2}`.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CACHE="$ROOT/.cache"
PDKS="$ROOT/pdks"

die() { echo "setup-env: error: $*" >&2; exit 1; }
log() { echo "setup-env: $*"; }

sha256_of() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
    else die "no sha256 command found (need sha256sum or shasum)"; fi
}

# fetch_verified <url> <expected-sha256> <dest>: download, verify, then move
# into place. A mismatch deletes the download and aborts; nothing unverified
# is ever left at <dest>.
fetch_verified() {
    local url="$1" want="$2" dest="$3" tmp got
    tmp="$(mktemp "${dest}.XXXXXX")"
    curl -fsSL -o "$tmp" "$url" || { rm -f "$tmp"; die "download failed: $url"; }
    got="$(sha256_of "$tmp")"
    if [[ "$got" != "$want" ]]; then
        rm -f "$tmp"
        die "checksum mismatch for $url
  expected: $want
  actual:   $got"
    fi
    mv "$tmp" "$dest"
}

# json_get <file> <dotted.key>: print one value from a pin file.
json_get() {
    python3 -I - "$1" "$2" <<'PY'
import json, sys
v = json.load(open(sys.argv[1]))
for k in sys.argv[2].split("."):
    v = v[k]
print(v if not isinstance(v, (list, dict)) else json.dumps(v))
PY
}

# Lets tests exercise fetch_verified without running the whole setup.
if [[ "${SETUP_ENV_SOURCE_ONLY:-0}" == "1" ]]; then return 0 2>/dev/null || exit 0; fi

command -v python3 >/dev/null || die "python3 not found"
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' \
    || die "python >= $(json_get "$ROOT/sim/toolchain.json" python.floor) required"
for t in curl tar make gcc bison flex; do
    command -v "$t" >/dev/null || die "missing build/fetch tool: $t"
done

PDK_COMMIT="$(json_get "$ROOT/sim/pdk.json" pinned_commit)"
PDK_SHA="$(json_get "$ROOT/sim/pdk.json" tarball_sha256)"
G2_SHA="$(json_get "$ROOT/sim/pdk.json" sibling.tarball_sha256)"
KLT_COMMIT="$(json_get "$ROOT/layout/toolchain.json" klt.commit)"
KLT_SPEC="$(json_get "$ROOT/layout/toolchain.json" klt.install_spec)"
SCRIPT_BASE="$(json_get "$ROOT/layout/toolchain.json" klt_fetch_scripts.base_url)"
NG_VER="$(json_get "$ROOT/sim/toolchain.json" ngspice.pinned_version)"
NG_FLOOR="$(json_get "$ROOT/sim/toolchain.json" ngspice.floor_major)"
NG_URL="$(json_get "$ROOT/sim/toolchain.json" ngspice.tarball_url)"
NG_SHA="$(json_get "$ROOT/sim/toolchain.json" ngspice.tarball_sha256)"
NG_PREFIX="$ROOT/$(json_get "$ROOT/sim/toolchain.json" ngspice.install_prefix)"
OVA_TAG="$(json_get "$ROOT/sim/toolchain.json" openvaf.tag)"
OVA_SHA="$(json_get "$ROOT/sim/toolchain.json" openvaf.sha256)"
OVA_PREFIX="$ROOT/$(json_get "$ROOT/sim/toolchain.json" openvaf.install_prefix)"

KLT_HOME="$CACHE/klt"          # REPO_ROOT as the klayout-tools scripts see it
mkdir -p "$KLT_HOME/scripts" "$PDKS"
ln -sfn "$PDKS" "$KLT_HOME/pdks"

# 1. klayout-tools fetch scripts, by commit, sha256-checked.
log "fetching klayout-tools scripts @ ${KLT_COMMIT:0:12}"
while read -r name want; do
    dest="$KLT_HOME/scripts/$name"
    if [[ -f "$dest" && "$(sha256_of "$dest")" == "$want" ]]; then continue; fi
    fetch_verified "$SCRIPT_BASE/$name" "$want" "$dest"
    chmod +x "$dest"
done < <(python3 -I -c 'import json,sys; [print(k, v) for k, v in json.load(open(sys.argv[1]))["klt_fetch_scripts"]["sha256"].items() if not k.startswith("_c")]' "$ROOT/layout/toolchain.json")

# 2. The pins in sim/ must agree with the scripts that act on them.
grep -q "IHP_SG13CMOS5L_COMMIT=\"$PDK_COMMIT\"" "$KLT_HOME/scripts/fetch-ihp-sg13cmos5l.sh" \
    || die "sim/pdk.json pinned_commit disagrees with fetch-ihp-sg13cmos5l.sh"
grep -q "IHP_SG13CMOS5L_SHA256=\"$PDK_SHA\"" "$KLT_HOME/scripts/fetch-ihp-sg13cmos5l.sh" \
    || die "sim/pdk.json tarball_sha256 disagrees with fetch-ihp-sg13cmos5l.sh"
grep -q "IHP_OPEN_PDK_SHA256=\"$G2_SHA\"" "$KLT_HOME/scripts/fetch-ihp-sg13g2.sh" \
    || die "sim/pdk.json sibling.tarball_sha256 disagrees with fetch-ihp-sg13g2.sh"
grep -q "OPENVAF_R_TAG=\"$OVA_TAG\"" "$KLT_HOME/scripts/fetch-sg13g2-sim-toolchain.sh" \
    || die "sim/toolchain.json openvaf.tag disagrees with fetch-sg13g2-sim-toolchain.sh"
grep -q "OPENVAF_R_SHA256=\"$OVA_SHA\"" "$KLT_HOME/scripts/fetch-sg13g2-sim-toolchain.sh" \
    || die "sim/toolchain.json openvaf.sha256 disagrees with fetch-sg13g2-sim-toolchain.sh"

# 3. PDK: SG13G2 sibling first (the CMOS5L symlinks point into it), then CMOS5L.
#    Each script verifies its own tarball sha256 and exits non-zero on mismatch.
log "fetching PDK sibling ihp-sg13g2 and ihp-sg13cmos5l @ ${PDK_COMMIT:0:12}"
bash "$KLT_HOME/scripts/fetch-ihp-sg13g2.sh"
bash "$KLT_HOME/scripts/fetch-ihp-sg13cmos5l.sh"   # warns on the known dangling links; exit 0
PDK_ROOT="$PDKS/ihp-open-pdk"
CMOS5L="$PDK_ROOT/ihp-sg13cmos5l"
[[ "$(cat "$CMOS5L/.fetched-version")" == "$PDK_COMMIT" ]] \
    || die "installed ihp-sg13cmos5l is not at the pinned commit $PDK_COMMIT"

# The smoke bench needs the LV MOS corner library and the Verilog-A sources it
# builds from; fail with a clear message if the sibling does not provide them.
for need in libs.tech/ngspice/models/cornerMOSlv.lib libs.tech/ngspice/models/sg13g2_moslv_mod.lib \
            libs.tech/verilog-a/psp103/psp103.va libs.tech/verilog-a/r3_cmc/r3_cmc.va \
            libs.tech/verilog-a/mosvar/mosvar.va libs.tech/verilog-a/cap_cmomi/cap_cmomi.va; do
    [[ -e "$CMOS5L/$need" ]] || die "dangling or missing PDK file: ihp-sg13cmos5l/$need
  (a shared model is a relative symlink into the ihp-sg13g2 sibling; is the sibling present and complete?)"
done

# 4. ngspice >= floor: use PATH's if new enough, else build the pinned one here.
ng_major() { "$1" --version 2>/dev/null | sed -n 's/.*ngspice-\([0-9][0-9]*\).*/\1/p' | head -1; }
NGSPICE=""
if command -v ngspice >/dev/null 2>&1 && [[ "$(ng_major "$(command -v ngspice)")" -ge "$NG_FLOOR" ]] 2>/dev/null; then
    NGSPICE="$(command -v ngspice)"
elif [[ -x "$NG_PREFIX/bin/ngspice" ]]; then
    NGSPICE="$NG_PREFIX/bin/ngspice"
else
    log "ngspice >= $NG_FLOOR not on PATH; building pinned ngspice-$NG_VER into $NG_PREFIX (make -j${SETUP_JOBS:-2})"
    bld="$CACHE/ngspice-build"; mkdir -p "$bld"
    fetch_verified "$NG_URL" "$NG_SHA" "$bld/ngspice-$NG_VER.tar.gz"
    tar -xzf "$bld/ngspice-$NG_VER.tar.gz" -C "$bld"
    flags="$(python3 -I -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["ngspice"]["configure_flags"]))' "$ROOT/sim/toolchain.json")"
    ( cd "$bld/ngspice-$NG_VER" \
        && ./configure --prefix="$NG_PREFIX" $flags >"$bld/configure.log" 2>&1 \
        && nice make -j"${SETUP_JOBS:-2}" >"$bld/make.log" 2>&1 \
        && make install >"$bld/install.log" 2>&1 ) \
        || die "ngspice build failed; see $bld/*.log"
    NGSPICE="$NG_PREFIX/bin/ngspice"
fi
[[ "$(ng_major "$NGSPICE")" -ge "$NG_FLOOR" ]] || die "ngspice at $NGSPICE is below the OSDI floor ($NG_FLOOR)"
log "ngspice: $("$NGSPICE" --version | sed -n 's/.*\(ngspice-[0-9]*\).*/\1/p' | head -1) ($NGSPICE)"

# 5. OpenVAF-Reloaded + SG13G2 sibling OSDI (the klayout-tools script also
#    checks the ngspice ABI floor and load-tests each model), then the CMOS5L
#    models, including cap_cmomi/cap_cmomf, with the PDK's own compile script.
export OPENVAF_R_INSTALL_PREFIX="$OVA_PREFIX"
PATH="$(dirname "$NGSPICE"):$PATH" bash "$KLT_HOME/scripts/fetch-sg13g2-sim-toolchain.sh"
OSDI_DIR="$CMOS5L/libs.tech/ngspice/osdi"
want_osdi=(psp103 psp103_nqs r3_cmc mosvar cap_cmomi cap_cmomf)
missing=0; for m in "${want_osdi[@]}"; do [[ -f "$OSDI_DIR/$m.osdi" ]] || missing=1; done
if [[ $missing -eq 1 ]]; then
    log "compiling ihp-sg13cmos5l Verilog-A models to OSDI"
    ( cd "$CMOS5L/libs.tech/verilog-a" && PATH="$OVA_PREFIX/bin:$PATH" ./openvaf-compile-va.sh ) \
        || die "OSDI build failed"
fi
for m in "${want_osdi[@]}"; do
    [[ -f "$OSDI_DIR/$m.osdi" ]] || die "OSDI model not built: $m.osdi"
    deck="$(mktemp --suffix=.cir)"
    printf '* osdi load check\n.control\npre_osdi %s\ndevhelp\nquit\n.endc\n.end\n' "$OSDI_DIR/$m.osdi" >"$deck"
    out="$("$NGSPICE" -b "$deck" 2>&1)" || { rm -f "$deck"; die "ngspice failed loading $m.osdi: $out"; }
    rm -f "$deck"
    if grep -qiE "only supports OSDI|couldn't be loaded|undefined symbol" <<<"$out"; then
        die "ngspice cannot load $m.osdi"
    fi
    log "OSDI ok: $m.osdi"
done

# 6. klt at the pinned commit, in a venv inside the checkout.
VENV="$ROOT/.venv"
want_tag="g${KLT_COMMIT:0:12}"
if [[ ! -x "$VENV/bin/klt" ]] || ! "$VENV/bin/klt" --version 2>/dev/null | grep -q "$want_tag"; then
    command -v uv >/dev/null || die "uv not found (needed to create the klt venv)"
    log "installing klt @ ${KLT_COMMIT:0:12} into $VENV"
    uv venv --quiet "$VENV"
    uv pip install --quiet --python "$VENV/bin/python" "$KLT_SPEC"
fi
"$VENV/bin/klt" --version | grep -q "$want_tag" \
    || die "klt in $VENV is not at the pinned commit ${KLT_COMMIT:0:12}"
for c in $(python3 -I -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["klt"]["klt_required_commands"]))' "$ROOT/layout/toolchain.json"); do
    "$VENV/bin/klt" "$c" --help >/dev/null 2>&1 || die "klt lacks required command: $c"
done
log "klt: $("$VENV/bin/klt" --version)"

# 7. Environment file to source.
cat >"$CACHE/env.sh" <<EOF
# Generated by scripts/setup-env.sh -- do not edit.
export PDK_ROOT="$PDK_ROOT"
export PDK=ihp-sg13cmos5l
export PATH="$VENV/bin:$(dirname "$NGSPICE"):$OVA_PREFIX/bin:\$PATH"
EOF
log "done. Next: source .cache/env.sh"
